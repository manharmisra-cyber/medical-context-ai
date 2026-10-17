"""Build review-only MONDO -> HPOA name candidates. No identity approval."""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

import torch

from medical_context_ai.scripts.medical_data import get_medical_data
from medical_context_ai.knowledge.identity import normalize_external_id
from medical_context_ai.terminology.mondo_matcher import MondoDiseaseMatcher


def read_hpoa_names(path):
    """HPOA columns normally include database_id and disease_name."""
    with open(path, encoding='utf-8-sig', newline='') as f:
        header = None
        for line in f:
            if line.startswith('#'):
                possible = line.lstrip('#').strip().split('\t')
                if 'database_id' in possible and 'disease_name' in possible:
                    header = possible
                continue
            values = line.rstrip('\r\n').split('\t')
            if header is None:
                if 'database_id' in values and 'disease_name' in values:
                    header = values
                    continue
                raise ValueError('HPOA file lacks database_id/disease_name header')
            row = dict(zip(header, values))
            identifier = normalize_external_id(row.get('database_id', ''))
            name = row.get('disease_name', '').strip()
            if identifier and name:
                yield identifier, name


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cores', type=int, default=None)
    p.add_argument('--batch-size', type=int, default=64)
    p.add_argument('--top-k', type=int, default=5)
    p.add_argument('--query-batch', type=int, default=128)
    p.add_argument('--all', action='store_true', help='Include MONDO diseases already directly mapped')
    args = p.parse_args()
    root = Path(__file__).resolve().parents[3]
    graph, associations, _, resolver = get_medical_data()
    names = defaultdict(set)
    for identifier, name in read_hpoa_names(root / 'data/external/phenotype.hpoa'):
        if identifier:
            names[identifier].add(name)
    valid_ids = {normalize_external_id(k) for k in associations}
    names = {k: sorted(v) for k, v in names.items() if k in valid_ids}
    if not names:
        raise RuntimeError('No HPOA disease names extracted; inspect phenotype.hpoa header')
    direct = defaultdict(set)
    for source in associations:
        mondo = resolver.resolve(source)
        if mondo:
            direct[mondo].add(normalize_external_id(source))
    target_ids = sorted(graph.nodes if args.all else set(graph.nodes) - set(direct))
    matcher = MondoDiseaseMatcher(graph, cache_dir=root / 'data/cache', batch_size=args.batch_size, cpu_cores=args.cores)
    # Encode each distinct HPOA name once. IDs may share names.
    name_to_ids = defaultdict(set)
    for identifier, variants in names.items():
        for name in variants:
            name_to_ids[name].add(identifier)
    hpoa_names = sorted(name_to_ids)
    print(f'Encoding {len(hpoa_names):,} HPOA names; matching {len(target_ids):,} MONDO IDs')
    hpoa_vectors = matcher._encode(hpoa_names)
    # MONDO label + synonym vectors already cached. Compute best HPOA candidates per MONDO
    # without allocating the full MONDO x HPOA similarity matrix.
    target_ids_set = set(target_ids)
    by_mondo = defaultdict(list)
    for i, entry in enumerate(matcher.entries):
        if entry['mondo_id'] in target_ids_set:
            by_mondo[entry['mondo_id']].append(i)
    output = root / 'data/cache/mondo_hpoa_semantic_candidates.tsv'
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['mondo_id','mondo_name','hpoa_id','hpoa_name','similarity','match_type','status'])
        for start in range(0, len(target_ids), args.query_batch):
            ids = target_ids[start:start + args.query_batch]
            # A MONDO concept may have several indexed synonyms. Pool by maximum score.
            index = [idx for mid in ids for idx in by_mondo[mid]]
            if not index:
                continue
            scores = matcher.embeddings[index] @ hpoa_vectors.T
            offset = 0
            for mid in ids:
                count = len(by_mondo[mid])
                per_name_scores = scores[offset:offset+count]
                offset += count
                best_scores, best_synonym_idx = per_name_scores.max(dim=0)
                # Deduplicate by HPOA ID; multiple disease names can share identifiers.
                ranked = torch.topk(best_scores, k=min(len(hpoa_names), max(50, args.top_k * 20))).indices
                seen = set()
                for j in ranked.tolist():
                    phrase = hpoa_names[j]
                    for source_id in sorted(name_to_ids[phrase]):
                        if source_id in seen:
                            continue
                        seen.add(source_id)
                        matched_mondo_phrase = matcher.entries[by_mondo[mid][best_synonym_idx[j].item()]]['phrase']
                        exact = matched_mondo_phrase.casefold() == phrase.casefold()
                        match_type = 'EXACT_NAME_OR_SYNONYM' if exact else 'SEMANTIC'
                        writer.writerow([mid, graph.nodes[mid].label, source_id, phrase, round(best_scores[j].item(), 5), match_type, 'UNVERIFIED_CANDIDATE'])
                        if len(seen) >= args.top_k:
                            break
                    if len(seen) >= args.top_k:
                        break
            print(f'Processed {min(start + len(ids), len(target_ids)):,}/{len(target_ids):,} MONDO concepts', flush=True)
    print(f'Candidate report: {output}')
    print('These are name-similarity suggestions, NOT approved disease identities or phenotype annotations.')


if __name__ == '__main__':
    main()
