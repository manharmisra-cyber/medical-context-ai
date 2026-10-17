"""Read-only BODHI-S condition/symptom association importer and MONDO mapping audit.

Run: python -m medical_context_ai.scripts.import_bodhi_associations

Exports candidates, NOT verified MONDO phenotype annotations. No HPOA modification.
"""
import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from medical_context_ai.scripts.medical_data import get_medical_data
from medical_context_ai.knowledge.identity import normalize_external_id


BASE = Path('data/external/bodhi-s/csv')
OUT = Path('data/cache/bodhi_audit')


def read_csv(path, required):
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = set(required) - fields
        if missing:
            raise ValueError(f'{path}: missing columns {sorted(missing)}')
        return list(reader)


def write_tsv(path, columns, records):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter='\t', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=BASE)
    parser.add_argument('--output-dir', type=Path, default=OUT)
    parser.add_argument('--samples', type=int, default=10)
    args = parser.parse_args()

    conditions = read_csv(args.data_dir / 'nodes_condition.csv', ['snomed_id', 'name', 'concept_type', 'type_condition'])
    symptoms = read_csv(args.data_dir / 'nodes_symptom.csv', ['uuid', 'name', 'root_snomed_id', 'root_snomed_name'])
    edges = read_csv(args.data_dir / 'edges_present_in.csv', [
        'symptom_uuid', 'condition_snomed_id', 'likelihood_symptom_given_condition',
        'likelihood_condition_given_symptom', 'strong_predictor'
    ])

    condition_by_id = {r['snomed_id'].strip(): r for r in conditions}
    symptom_by_id = {r['uuid'].strip(): r for r in symptoms}
    if len(condition_by_id) != len(conditions) or len(symptom_by_id) != len(symptoms):
        raise ValueError('Duplicate condition SNOMED IDs or symptom UUIDs detected')

    graph, hpoa, _, resolver = get_medical_data()
    hpoa_linked = {
        mid for source in hpoa
        if (mid := resolver.resolve(normalize_external_id(source))) in graph.nodes
    }
    sctid_to_mondo = defaultdict(set)
    for mondo_id, node in graph.nodes.items():
        for xref in node.metadata.get('xrefs', []) or []:
            prefix, sep, value = str(xref).strip().partition(':')
            if sep and prefix.upper() in {'SCTID', 'SNOMEDCT', 'SNOMEDCT_US', 'SNOMED'}:
                sctid_to_mondo[value].add(mondo_id)

    rows = []
    problems = Counter()
    for edge in edges:
        cid = edge['condition_snomed_id'].strip()
        sid = edge['symptom_uuid'].strip()
        condition = condition_by_id.get(cid)
        symptom = symptom_by_id.get(sid)
        if condition is None:
            problems['missing_condition'] += 1
        if symptom is None:
            problems['missing_symptom'] += 1
        if condition is None or symptom is None:
            continue
        mondo_ids = sorted(sctid_to_mondo.get(cid, ()))
        for mid in mondo_ids or ['']:
            rows.append({
                'mondo_id': mid,
                'mondo_name': graph.nodes[mid].label if mid else '',
                'mondo_has_direct_hpoa': str(mid in hpoa_linked) if mid else '',
                'mapping_status': 'UNVERIFIED_SCTID_XREF' if mid else 'NO_MONDO_XREF',
                'bodhi_condition_sctid': cid,
                'bodhi_condition_name': condition['name'],
                'bodhi_concept_type': condition.get('concept_type', ''),
                'bodhi_condition_type': condition.get('type_condition', ''),
                'bodhi_symptom_uuid': sid,
                'bodhi_symptom_name': symptom['name'],
                'bodhi_symptom_sctid': symptom.get('snomed_id', ''),
                'bodhi_root_symptom_sctid': symptom['root_snomed_id'],
                'bodhi_root_symptom_name': symptom['root_snomed_name'],
                'likelihood_symptom_given_condition': edge['likelihood_symptom_given_condition'],
                'likelihood_condition_given_symptom': edge['likelihood_condition_given_symptom'],
                'strong_predictor': edge['strong_predictor'],
                'source': 'BODHI-S',
                'evidence_status': 'SOURCE_ASSERTION_NOT_INDEPENDENTLY_VALIDATED',
            })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / 'bodhi_mondo_association_candidates.tsv'
    fields = list(rows[0]) if rows else [
        'mondo_id', 'mondo_name', 'mondo_has_direct_hpoa', 'mapping_status',
        'bodhi_condition_sctid', 'bodhi_condition_name', 'bodhi_concept_type',
        'bodhi_condition_type', 'bodhi_symptom_uuid', 'bodhi_symptom_name',
        'bodhi_symptom_sctid', 'bodhi_root_symptom_sctid', 'bodhi_root_symptom_name',
        'likelihood_symptom_given_condition', 'likelihood_condition_given_symptom',
        'strong_predictor', 'source', 'evidence_status'
    ]
    write_tsv(output, fields, rows)

    linked_rows = [r for r in rows if r['mondo_id']]
    new_mondo = {r['mondo_id'] for r in linked_rows if r['mondo_has_direct_hpoa'] == 'False'}
    linked_conditions = {r['bodhi_condition_sctid'] for r in linked_rows}
    print('\n========== BODHI-S ASSOCIATION IMPORT AUDIT ==========')
    print(f'Conditions: {len(conditions):,}; symptoms: {len(symptoms):,}; edges: {len(edges):,}')
    print(f'Valid source edges: {len(edges) - sum(problems.values()):,} (see reference errors below)')
    print(f'Exported candidate rows: {len(rows):,}')
    print(f'Rows with MONDO SCTID candidate: {len(linked_rows):,}')
    print(f'BODHI conditions with MONDO candidate and at least one edge: {len(linked_conditions):,}')
    print(f'MONDO concepts without direct HPOA gaining candidate edges: {len(new_mondo):,}')
    print(f'Reference errors: {dict(problems)}')
    print('Mapping status: UNVERIFIED. No phenotype transfers or diagnostic ranking changes.')
    print(f'Export: {output}')
    print('\nSample candidate associations:')
    for row in linked_rows[:max(0, args.samples)]:
        print(f"  {row['mondo_id']} | {row['bodhi_condition_name']} -> "
              f"{row['bodhi_symptom_name']} ({row['likelihood_symptom_given_condition']})")


if __name__ == '__main__':
    main()
