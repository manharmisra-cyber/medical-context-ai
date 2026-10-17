"""Audit HPOA -> MONDO coverage and why MONDO -> HPOA CLI lookups can be empty."""
from collections import Counter, defaultdict
from pathlib import Path

from medical_context_ai.scripts.medical_data import get_medical_data
from medical_context_ai.knowledge.identity import normalize_external_id, build_identity_resolver
from medical_context_ai.knowledge.sssom_importer import load_sssom_mappings


def main():
    graph, associations, terms, resolver = get_medical_data()
    root = Path(__file__).resolve().parents[3]
    sssom, conflicts = load_sssom_mappings(
        root / 'data' / 'external' / 'mondo.sssom.tsv', set(graph.nodes)
    )
    baseline = build_identity_resolver(graph)
    normalized = defaultdict(set)
    for source_id in associations:
        normalized[normalize_external_id(source_id)].add(source_id)

    current_by_mondo = defaultdict(set)
    baseline_by_mondo = defaultdict(set)
    sssom_by_mondo = defaultdict(set)
    unresolved = []
    discrepancies = []
    added = []
    for external_id, original_ids in normalized.items():
        current = resolver.resolve(external_id)
        old = baseline.resolve(external_id)
        mapped = sssom.get(external_id)
        if current:
            current_by_mondo[current].update(original_ids)
        else:
            unresolved.append(external_id)
        if old:
            baseline_by_mondo[old].update(original_ids)
        if mapped:
            sssom_by_mondo[mapped].update(original_ids)
        if current and not old:
            added.append(external_id)
        if mapped and current != mapped:
            discrepancies.append((external_id, mapped, current))

    mondo_without_hpoa = sorted(set(graph.nodes) - set(current_by_mondo))
    print('\n========== SSSOM / CLI IMPACT ==========')
    print(f'MONDO nodes: {len(graph.nodes):,}')
    print(f'HPOA unique normalized disease IDs: {len(normalized):,}')
    print(f'SSSOM mappings loaded: {len(sssom):,}; importer conflicts: {len(conflicts):,}')
    print(f'HPOA IDs present in SSSOM: {len(set(normalized) & set(sssom)):,}')
    print(f'HPOA IDs resolved by current resolver: {sum(bool(resolver.resolve(x)) for x in normalized):,}')
    print(f'HPOA IDs resolved by baseline (no SSSOM): {sum(bool(baseline.resolve(x)) for x in normalized):,}')
    print(f'HPOA IDs newly resolved vs baseline: {len(added):,}')
    print(f'HPOA IDs unresolved by current resolver: {len(unresolved):,}')
    print(f'MONDO nodes with linked HPOA IDs: {len(current_by_mondo):,}')
    print(f'MONDO nodes with NO linked HPOA IDs: {len(mondo_without_hpoa):,}')
    print(f'SSSOM/current resolver disagreements: {len(discrepancies):,}')

    print('\nUNRESOLVED HPOA IDENTIFIERS (first 50):')
    for x in sorted(unresolved)[:50]:
        print(' ', x, 'xref candidates:', ', '.join(sorted(resolver.candidates.get(x, ()))) or 'none')

    print('\nMONDO IDS WITHOUT HPOA LINKS (first 50):')
    for mondo_id in mondo_without_hpoa[:50]:
        node = graph.nodes[mondo_id]
        print(f'  {mondo_id} | {node.label}')

    print('\nSSSOM/CURRENT DISAGREEMENTS (first 20):')
    for row in discrepancies[:20]:
        print(' ', row)

    print('\nCLI TEST: type a MONDO ID or part of a disease name; blank to quit.')
    while True:
        query = input('MONDO/name> ').strip()
        if not query:
            break
        hits = [node for node in graph.nodes.values() if query.casefold() in node.label.casefold() or query.upper() == node.id][:10]
        if not hits:
            print('No MONDO name/ID match')
            continue
        for node in hits:
            source_ids = sorted(current_by_mondo.get(node.id, ()))
            hp_ids = set()
            for source_id in source_ids:
                hp_ids.update(associations[source_id])
            print(f'{node.id} | {node.label} | HPOA source IDs: {len(source_ids)} | HPO terms: {len(hp_ids)}')
            print('  linked IDs:', ', '.join(source_ids[:8]) or '(none)')
            if not source_ids:
                print('  Reason: no HPOA source ID resolves to this MONDO ID; could be absent annotations or an identity gap.')


if __name__ == '__main__':
    main()
