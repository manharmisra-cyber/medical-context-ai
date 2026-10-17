"""Compare BODHI conditions lacking MONDO SCTID xrefs against HPOA, MONDO
exact names/synonyms, existing BODHI-MONDO xrefs and optional SapBERT MONDO.

Review-only: never asserts identity or imports phenotypes.
Run: python -m medical_context_ai.scripts.audit_unmapped_bodhi
     python -m medical_context_ai.scripts.audit_unmapped_bodhi --sapbert --top-k 3
"""
import argparse
import csv
import re
from collections import defaultdict, Counter
from pathlib import Path

from medical_context_ai.scripts.medical_data import get_medical_data
from medical_context_ai.knowledge.identity import normalize_external_id

ROOT = Path(__file__).resolve().parents[3]


def normalized_name(value):
    return re.sub(r'\s+', ' ', re.sub(r'[^\w]+', ' ', str(value).casefold())).strip()


def read_table(path, required):
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'{path}: missing columns {sorted(missing)}')
        return list(reader)


def hpoa_disease_names(path):
    """HPOA header is commonly prefixed with #; support either convention."""
    header = None
    with path.open(encoding='utf-8-sig') as f:
        for line in f:
            parts = line.rstrip('\r\n').lstrip('#').strip().split('\t')
            if header is None:
                if 'database_id' in parts and 'disease_name' in parts:
                    header = parts
                continue
            if line.startswith('#') or not line.strip():
                continue
            row = dict(zip(header, line.rstrip('\r\n').split('\t')))
            name = row.get('disease_name', '').strip()
            source = normalize_external_id(row.get('database_id', '').strip())
            if name and source:
                yield source, name
    if header is None:
        raise ValueError(f'No database_id/disease_name header in {path}')


def synonym_text(value):
    if isinstance(value, dict):
        return str(value.get('label') or value.get('name') or value.get('text') or '')
    return str(value or '')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--conditions', type=Path, default=ROOT / 'data/external/bodhi-s/csv/nodes_condition.csv')
    p.add_argument('--hpoa', type=Path, default=ROOT / 'data/external/phenotype.hpoa')
    p.add_argument('--output', type=Path, default=ROOT / 'data/cache/bodhi_audit/unmapped_bodhi_comparison.tsv')
    p.add_argument('--sapbert', action='store_true', help='Run expensive MONDO SapBERT retrieval for unresolved BODHI names')
    p.add_argument('--top-k', type=int, default=3)
    p.add_argument('--min-score', type=float, default=0.0, help='Reporting filter only, NOT a validated identity threshold')
    p.add_argument('--samples', type=int, default=20)
    args = p.parse_args()
    if args.top_k < 1:
        p.error('--top-k must be >= 1')

    conditions = read_table(args.conditions, ['snomed_id', 'name', 'concept_type', 'type_condition'])
    graph, associations, _, resolver = get_medical_data()

    sctid_to_mondo = defaultdict(set)
    mondo_name_index = defaultdict(set)
    for mid, node in graph.nodes.items():
        for xref in node.metadata.get('xrefs', []) or []:
            prefix, sep, val = str(xref).strip().partition(':')
            if sep and prefix.upper() in {'SCTID', 'SNOMEDCT', 'SNOMEDCT_US', 'SNOMED'}:
                sctid_to_mondo[val].add(mid)
        synonyms = node.metadata.get('synonyms', []) or []
        if isinstance(synonyms, (str, dict)):
            synonyms = [synonyms]
        for phrase in [node.label, *(synonym_text(x) for x in synonyms)]:
            if normalized_name(phrase):
                mondo_name_index[normalized_name(phrase)].add(mid)

    hpoa_names = defaultdict(set)
    for source, name in hpoa_disease_names(args.hpoa):
        hpoa_names[normalized_name(name)].add(source)

    # These are verified source-ID resolutions only to the extent the existing
    # resolver has already verified them. Name matches alone are not identities.
    direct_hpoa = defaultdict(set)
    for source in associations:
        mid = resolver.resolve(normalize_external_id(source))
        if mid in graph.nodes:
            direct_hpoa[mid].add(normalize_external_id(source))

    unmatched = []
    for condition in conditions:
        sid = condition['snomed_id'].strip()
        if sctid_to_mondo.get(sid):
            continue
        name = condition['name'].strip()
        key = normalized_name(name)
        exact_mondo = sorted(mondo_name_index.get(key, ()))
        hpo_ids = sorted(hpoa_names.get(key, ()))
        hpo_mondo = sorted({mid for source in hpo_ids if (mid := resolver.resolve(source)) in graph.nodes})
        unmatched.append({
            'bodhi_sctid': sid, 'bodhi_name': name,
            'concept_type': condition.get('concept_type', ''),
            'condition_type': condition.get('type_condition', ''),
            'existing_bodhi_mondo_sctid': '',
            'hpoa_exact_name_ids': ';'.join(hpo_ids),
            'hpoa_exact_name_mondo_ids': ';'.join(hpo_mondo),
            'mondo_exact_label_or_synonym_ids': ';'.join(exact_mondo),
            'sapbert_mondo_candidates': '',
            'sapbert_best_similarity': '',
            'review_status': 'CANDIDATE_ONLY' if (hpo_ids or exact_mondo) else 'NO_DETERMINISTIC_NAME_MATCH',
        })

    if args.sapbert and unmatched:
        from medical_context_ai.terminology.mondo_matcher import MondoDiseaseMatcher
        matcher = MondoDiseaseMatcher(graph, cache_dir=ROOT / 'data/cache')
        for i, row in enumerate(unmatched, 1):
            # Even when an exact name exists, semantic results can help inspect
            # conflicting concepts, but never automatically approve a mapping.
            results = [r for r in matcher.search(row['bodhi_name'], top_k=args.top_k)
                       if r['similarity'] >= args.min_score]
            row['sapbert_mondo_candidates'] = ';'.join(
                f"{r['mondo_id']}|{r['similarity']:.4f}|{r['matched_phrase']}" for r in results
            )
            if results:
                row['sapbert_best_similarity'] = str(results[0]['similarity'])
            if i % 50 == 0:
                print(f'SapBERT checked {i:,}/{len(unmatched):,} unmapped conditions', flush=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(unmatched[0]) if unmatched else [
            'bodhi_sctid', 'bodhi_name', 'concept_type', 'condition_type',
            'existing_bodhi_mondo_sctid', 'hpoa_exact_name_ids',
            'hpoa_exact_name_mondo_ids', 'mondo_exact_label_or_synonym_ids',
            'sapbert_mondo_candidates', 'sapbert_best_similarity', 'review_status'
        ], delimiter='\t')
        writer.writeheader()
        writer.writerows(unmatched)

    counts = Counter()
    for row in unmatched:
        if row['hpoa_exact_name_ids']:
            counts['hpoa_name'] += 1
        if row['hpoa_exact_name_mondo_ids']:
            counts['hpoa_to_mondo'] += 1
        if row['mondo_exact_label_or_synonym_ids']:
            counts['mondo_name'] += 1
        if row['sapbert_mondo_candidates']:
            counts['sapbert'] += 1
        if row['hpoa_exact_name_ids'] or row['mondo_exact_label_or_synonym_ids']:
            counts['any_deterministic'] += 1
    print('\n========== UNMAPPED BODHI CROSS-SOURCE AUDIT ==========')
    print(f'BODHI conditions: {len(conditions):,}')
    print(f'Already linked by SCTID: {len(conditions) - len(unmatched):,}')
    print(f'Unmapped by SCTID: {len(unmatched):,}')
    print(f'Unmapped with exact HPOA disease name: {counts["hpoa_name"]:,}')
    print(f'  ...whose HPOA ID resolves to MONDO: {counts["hpoa_to_mondo"]:,}')
    print(f'Unmapped with exact MONDO label/synonym: {counts["mondo_name"]:,}')
    print(f'Unmapped with either deterministic name match: {counts["any_deterministic"]:,}')
    if args.sapbert:
        print(f'Unmapped with SapBERT candidates above reporting filter: {counts["sapbert"]:,}')
    else:
        print('SapBERT: skipped (add --sapbert to run)')
    print(f'Report: {args.output}')
    print('\nSample:')
    for row in unmatched[:max(0, args.samples)]:
        print(f"  {row['bodhi_name']} | HPOA: {row['hpoa_exact_name_ids'] or '-'} | "
              f"MONDO exact: {row['mondo_exact_label_or_synonym_ids'] or '-'} | "
              f"SapBERT: {row['sapbert_mondo_candidates'] or '-'}")
    print('\nCAUTION: All name/SapBERT results are review candidates, NOT verified disease identities.')


if __name__ == '__main__':
    main()
