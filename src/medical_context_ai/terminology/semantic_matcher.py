
import hashlib
import json
from pathlib import Path

import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer


MODEL_NAME = "cambridgeltl/SapBERT-from-PubMedBERT-fulltext"


class SemanticHPOMatcher:
    def __init__(
        self,
        hpo_terms: dict,
        cache_dir: str | Path = "data/cache",
        batch_size: int = 32,
    ):
        self.hpo_terms = hpo_terms
        self.batch_size = batch_size

        self.device = (
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        print(f"Loading SapBERT on {self.device}...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME
        )
        self.model = AutoModel.from_pretrained(
            MODEL_NAME
        ).to(self.device)

        self.model.eval()

        self.entries = []

        for hpo_id, term in hpo_terms.items():
            if isinstance(term, str):
                name = term
                synonyms = []
            elif isinstance(term, dict):
                name = term.get("name", "")
                synonyms = term.get("synonyms", [])
            else:
                name = getattr(term, "name", "")
                synonyms = getattr(term, "synonyms", [])

            if not name:
                continue

            for phrase in [name, *synonyms]:
                if isinstance(phrase, dict):
                    phrase = phrase.get("text", "")

                phrase = str(phrase).strip()

                if phrase:
                    self.entries.append(
                        {
                            "hpo_id": hpo_id,
                            "name": name,
                            "phrase": phrase,
                        }
                    )

        print(
            f"Indexed {len(self.entries):,} "
            "HPO labels and synonyms."
        )

        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)

        signature = hashlib.sha256(
            json.dumps(
                {
                    "model": MODEL_NAME,
                    "entries": self.entries,
                },
                sort_keys=True,
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()[:16]

        self.cache_path = (
            cache_dir / f"hpo_sapbert_{signature}.pt"
        )

        if self.cache_path.exists():
            print("Loading cached HPO embeddings...")
            self.embeddings = torch.load(
                self.cache_path,
                map_location="cpu",
                weights_only=True,
            )
        else:
            print("Building HPO embeddings...")
            phrases = [
                entry["phrase"]
                for entry in self.entries
            ]

            self.embeddings = self._encode(
                phrases
            ).cpu()

            torch.save(
                self.embeddings,
                self.cache_path,
            )

            print("Embedding cache saved.")

    @torch.inference_mode()
    def _encode(self, phrases: list[str]) -> torch.Tensor:
        vectors = []

        for start in range(
            0, len(phrases), self.batch_size
        ):
            batch = phrases[
                start:start + self.batch_size
            ]

            tokens = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=64,
                return_tensors="pt",
            )

            tokens = {
                key: value.to(self.device)
                for key, value in tokens.items()
            }

            output = self.model(**tokens)

            # SapBERT commonly uses CLS representations
            embeddings = output.last_hidden_state[:, 0, :]

            embeddings = F.normalize(
                embeddings,
                p=2,
                dim=1,
            )

            vectors.append(
                embeddings.cpu()
            )

            if len(phrases) > self.batch_size:
                done = min(
                    start + self.batch_size,
                    len(phrases),
                )
                if done % 1000 < self.batch_size:
                    print(
                        f"Encoded {done:,}/{len(phrases):,}"
                    )

        return torch.cat(vectors, dim=0)

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        if not query.strip() or not self.entries:
            return []

        query_vector = self._encode(
            [query]
        )[0]

        scores = self.embeddings @ query_vector

        # Multiple synonyms can point to the same HPO ID.
        # Keep only the strongest hit for each concept.
        ranked = torch.argsort(
            scores,
            descending=True,
        )

        results = []
        seen = set()

        for index in ranked.tolist():
            entry = self.entries[index]

            if entry["hpo_id"] in seen:
                continue

            seen.add(entry["hpo_id"])

            results.append(
                {
                    "hpo_id": entry["hpo_id"],
                    "name": entry["name"],
                    "matched_phrase": entry["phrase"],
                    "similarity": round(
                        float(scores[index]),
                        4,
                    ),
                }
            )

            if len(results) >= top_k:
                break

        return results
