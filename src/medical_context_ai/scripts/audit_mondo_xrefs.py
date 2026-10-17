"""Audit MONDO cross-references and gaps in direct HPOA coverage.

Run: python -m medical_context_ai.scripts.audit_mondo_xrefs
No network, no model inference, no mappings modified.
"""
import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from medical_context_ai.scripts.medical_data import get_medical_data
from medical_context_ai.knowledge.identity import normalize_external_id


def split_xref(value):
    value = str(value).strip()
    if not value:
        return None, None
    if value.startswith('http://id.who.int/icd/entity/'):
        return 'ICD11.FOUNDATION', value.rsplit('/', 1)[-1]
    if ':' not in value:
        return None, None
    prefix, local = value.split(':', 1)
    aliases = {
        'ORPHANET': 'ORPHA', 'ORPHA': 'ORPHA',
        'SNOMEDCT_US': 'SCTID', 'SNOMEDCT': 'SCTID',
        'SNOMED': 'SCTID', 'ICD11.FOUNDATION': 'ICD11.FOUNDATION',
    }
    prefix = aliases.get(prefix.upper(), prefix.upper())
    return (prefix, local) if local else (None, None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--top', type=int, default=25, help='Prefixes shown in terminal')
    parser.add_argument('--sample', type=int, default=10, help='Unlinked examples per prefix')
    args = parser.parse_args()
    graph, associations, _, resolver = get_medical_data()
    root = Path(__file__).resolve().parents[3]
    out = root / 'data' / 'cache' / 'xref_audit'
    out.mkdir(parents=True, exist_ok=True)

    linked = defaultdict(set)
    for source_id in associations:
        mid = resolver.resolve(normalize_external_id(source_id))
        if mid in graph.nodes:
            linked[mid].add(source_id)

    all_ids = set(graph.nodes)
    missing = all_ids - set(linked)
    per_prefix = defaultdict(set)
    missing_prefix = defaultdict(set)
    xref_rows = []
    per_node = {}
    for mid, node in sorted(graph.nodes.items()):
        raw = node.metadata.get('xrefs', []) or []
        if isinstance(raw, str):
            raw = [raw]
        prefixes = set()
        for xref in raw:
            prefix, local = split_xref(xref)
            if not prefix:
                continue
            prefixes.add(prefix)
            per_prefix[prefix].add(mid)
            if mid in missing:
                missing_prefix[prefix].add(mid)
            xref_rows.append((mid, node.label, str(xref), prefix, mid in linked))
        per_node[mid] = prefixes

    with (out / 'mondo_xrefs.tsv').open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t')
        w.writerow(['mondo_id', 'mondo_name', 'external_xref', 'source_prefix', 'has_direct_hpoa'])
        w.writerows(xref_rows)

    with (out / 'xref_source_coverage.tsv').open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t')
        w.writerow(['source_prefix', 'mondo_concepts_with_xref', 'without_direct_hpoa', 'with_direct_hpoa'])
        for prefix in sorted(per_prefix, key=lambda p: (-len(missing_prefix[p]), p)):
            w.writerow([prefix, len(per_prefix[prefix]), len(missing_prefix[prefix]),
                        len(per_prefix[prefix] - missing_prefix[prefix])])

    with (out / 'mondo_without_hpoa.tsv').open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t')
        w.writerow(['mondo_id', 'mondo_name', 'xref_count', 'xref_prefixes', 'xrefs'])
        for mid in sorted(missing):
            node = graph.nodes[mid]
            raw = node.metadata.get('xrefs', []) or []
            if isinstance(raw, str):
                raw = [raw]
            w.writerow([mid, node.label, len(raw), ';'.join(sorted(per_node[mid])), ';'.join(map(str, raw))])

    print('\n========== MONDO XREF COVERAGE AUDIT ==========')
    print(f'MONDO concepts: {len(all_ids):,}')
    print(f'With direct HPOA links: {len(linked):,}')
    print(f'Without direct HPOA links: {len(missing):,}')
    print(f'Without HPOA but with >=1 xref: {sum(bool(per_node[mid]) for mid in missing):,}')
    print(f'Without HPOA and without xrefs: {sum(not per_node[mid] for mid in missing):,}')
    print('\nSOURCE PREFIX | ALL MONDO | WITHOUT DIRECT HPOA')
    for prefix in sorted(per_prefix, key=lambda p: (-len(missing_prefix[p]), p))[:args.top]:
        print(f'{prefix:22} {len(per_prefix[prefix]):>10,} {len(missing_prefix[prefix]):>20,}')
    print('\nEXAMPLES OF UNLINKED MONDO CONCEPTS BY SOURCE')
    for prefix in sorted(per_prefix, key=lambda p: (-len(missing_prefix[p]), p))[:args.top]:
        if not missing_prefix[prefix]:
            continue
        print(f'\n{prefix}:')
        for mid in sorted(missing_prefix[prefix])[:args.sample]:
            node = graph.nodes[mid]
            matching = [x for x in (node.metadata.get('xrefs', []) or [])
                        if split_xref(x)[0] == prefix]
            print(f'  {mid} | {node.label} | {", ".join(map(str, matching[:3]))}')
    print(f'\nSaved reports to: {out}')
    print('Note: Cross-references are NOT automatically exact identity mappings.')
    print('Mapping predicates/qualifiers require a separate raw MONDO/SSSOM audit.')


if __name__ == '__main__':
    main()
