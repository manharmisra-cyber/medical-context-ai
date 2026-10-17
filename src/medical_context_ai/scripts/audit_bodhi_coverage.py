"""Audit BODHI-S condition coverage against MONDO, without importing clinical edges.

Usage:
 python -m medical_context_ai.scripts.audit_bodhi_coverage --conditions data/external/bodhi-s/csv/nodes_condition.csv
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

from medical_context_ai.scripts.medical_data import get_medical_data
from medical_context_ai.knowledge.identity import normalize_external_id


def snomed_id(raw):
    s = str(raw or '').strip()
    if not s or s.lower() in {'nan', 'none'}:
        return None
    return s.split(':', 1)[-1] if ':' in s else s


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--conditions', type=Path, required=True)
    p.add_argument('--top', type=int, default=20)
    args = p.parse_args()
    if not args.conditions.is_file():
        p.error(f'Not found: {args.conditions}')

    graph, associations, _, resolver = get_medical_data()
    linked = set()
    for source_id in associations:
        mid = resolver.resolve(normalize_external_id(source_id))
        if mid in graph.nodes:
            linked.add(mid)

    snomed_to_mondo = defaultdict(set)
    for mid, node in graph.nodes.items():
        xrefs = node.metadata.get('xrefs', []) or []
        if isinstance(xrefs, str):
            xrefs = [xrefs]
        for x in xrefs:
            x = str(x).strip()
            if ':' not in x:
                continue
            prefix, value = x.split(':', 1)
            if prefix.upper() in {'SCTID', 'SNOMEDCT', 'SNOMEDCT_US', 'SNOMED'}:
                snomed_to_mondo[value].add(mid)

    records = []
    with args.conditions.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not {'snomed_id', 'name'} <= set(reader.fieldnames):
            p.error(f'Expected snomed_id and name columns, got {reader.fieldnames}')
        for row in reader:
            sid = snomed_id(row.get('snomed_id'))
            candidates = sorted(snomed_to_mondo.get(sid, ())) if sid else []
            records.append((row.get('name', ''), sid, candidates))

    unique = {mid for _, _, ids in records for mid in ids}
    newly_covered = unique - linked
    ambiguous = [(name, sid, ids) for name, sid, ids in records if len(ids) > 1]
    unmatched = [(name, sid) for name, sid, ids in records if not ids]
    print('\n========== BODHI-S → MONDO COVERAGE (XREF CANDIDATES) ==========')
    print(f'BODHI-S condition rows: {len(records):,}')
    print(f'Rows with ≥1 MONDO SCTID xref: {sum(bool(ids) for _, _, ids in records):,}')
    print(f'Rows with no MONDO SCTID xref: {len(unmatched):,}')
    print(f'Rows mapping to multiple MONDO concepts: {len(ambiguous):,}')
    print(f'Distinct MONDO concepts reached: {len(unique):,}')
    print(f'Of these, MONDO concepts lacking direct HPOA: {len(newly_covered):,}')
    print('CAUTION: Xref matches are candidates, not verified identity or phenotype transfers.')
    print('\nExamples of new coverage candidates:')
    count = 0
    for name, sid, ids in records:
        for mid in ids:
            if mid in newly_covered:
                print(f'  {mid} | {graph.nodes[mid].label} | BODHI: {name} | SCTID:{sid}')
                count += 1
                if count >= args.top:
                    break
        if count >= args.top:
            break
    print('\nUnmatched BODHI conditions (sample):')
    for name, sid in unmatched[:args.top]:
        print(f'  {name} | SCTID:{sid}')
    print('\nNext: audit mapping predicates and condition→symptom edges before integration.')


if __name__ == '__main__':
    main()
