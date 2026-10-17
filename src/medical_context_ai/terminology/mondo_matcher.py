"""SapBERT retrieval of MONDO disease-name candidates; never approves identities."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer

MODEL_NAME = "cambridgeltl/SapBERT-from-PubMedBERT-fulltext"


def _synonym_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("label") or value.get("name") or value.get("text") or "")
    return str(value or "")


class MondoDiseaseMatcher:
    def __init__(self, graph, cache_dir="data/cache", batch_size=64, cpu_cores=None):
        self.batch_size = max(1, int(batch_size))
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if cpu_cores is None:
            cpu_cores = max(1, (os.cpu_count() or 2) - 2)
        self.cpu_cores = max(1, int(cpu_cores))
        torch.set_num_threads(self.cpu_cores)
        print(f"MONDO SapBERT: {self.device}, {self.cpu_cores} CPU threads")

        self.entries = []
        seen = set()
        for node in graph.nodes.values():
            metadata = getattr(node, "metadata", {}) or {}
            synonyms = metadata.get("synonyms", [])
            if isinstance(synonyms, (str, dict)):
                synonyms = [synonyms]
            for phrase in [node.label, *(_synonym_text(x) for x in synonyms)]:
                phrase = str(phrase or "").strip()
                key = (node.id, phrase.casefold())
                if phrase and key not in seen:
                    seen.add(key)
                    self.entries.append({"mondo_id": node.id, "name": node.label, "phrase": phrase})
        self.entries.sort(key=lambda e: (e["mondo_id"], e["phrase"].casefold()))
        if not self.entries:
            raise ValueError("MONDO graph contains no indexed disease labels")

        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        signature = hashlib.sha256(json.dumps({"model": MODEL_NAME, "entries": self.entries}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20]
        self.cache_path = cache_dir / f"mondo_sapbert_{signature}.pt"
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModel.from_pretrained(MODEL_NAME).to(self.device).eval()
        if self.cache_path.exists():
            print("Loading cached MONDO disease embeddings...")
            self.embeddings = torch.load(self.cache_path, map_location="cpu", weights_only=True)
            if self.embeddings.ndim != 2 or self.embeddings.shape[0] != len(self.entries):
                raise ValueError("Invalid MONDO embedding cache; remove it and rebuild")
        else:
            print(f"Encoding {len(self.entries):,} MONDO names/synonyms (first run only)...")
            self.embeddings = self._encode([e["phrase"] for e in self.entries])
            tmp = self.cache_path.with_suffix(".tmp")
            torch.save(self.embeddings, tmp)
            tmp.replace(self.cache_path)
            print(f"Cached MONDO embeddings: {self.cache_path}")

        self.exact_index = {}
        for e in self.entries:
            self.exact_index.setdefault(e["phrase"].casefold(), set()).add(e["mondo_id"])

    @torch.inference_mode()
    def _encode(self, phrases):
        chunks = []
        for start in range(0, len(phrases), self.batch_size):
            batch = phrases[start:start + self.batch_size]
            tokens = self.tokenizer(batch, padding=True, truncation=True, max_length=64, return_tensors="pt")
            tokens = {k: v.to(self.device) for k, v in tokens.items()}
            vectors = self.model(**tokens).last_hidden_state[:, 0, :]
            chunks.append(F.normalize(vectors.float(), p=2, dim=1).cpu())
            if len(phrases) > 1000 and (start // self.batch_size) % 50 == 0:
                print(f"  Encoded {min(start + len(batch), len(phrases)):,}/{len(phrases):,}")
        return torch.cat(chunks)

    def search(self, disease_name, top_k=5):
        query = disease_name.strip()
        if not query or top_k < 1:
            return []
        query_vec = self._encode([query])[0]
        scores = self.embeddings @ query_vec
        # Rank each MONDO concept by its best-matching name or synonym.
        best = {}
        for idx in torch.argsort(scores, descending=True).tolist():
            e = self.entries[idx]
            if e["mondo_id"] in best:
                continue
            best[e["mondo_id"]] = {
                "mondo_id": e["mondo_id"], "name": e["name"],
                "matched_phrase": e["phrase"],
                "similarity": round(float(scores[idx]), 4),
                "exact_name_or_synonym": query.casefold() == e["phrase"].casefold(),
                "status": "UNVERIFIED_CANDIDATE",
            }
            if len(best) >= top_k:
                break
        return list(best.values())
