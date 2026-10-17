"""Print a concise summary of an existing MONDO cross-reference audit."""
import argparse
import csv
from pathlib import Path


def read_tsv(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle, delimiter='\t'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--top', type=int, default=15)
    parser.add_argument('--dir', type=Path, default=Path('data/cache/xref_audit'))
    args = parser.parse_args()
    coverage = args.dir / 'xref_source_coverage.tsv'
    missing = args.dir / 'mondo_without_hpoa.tsv'
    for path in (coverage, missing):
        if not path.is_file():
            parser.error(f'Missing {path}. Run the audit first, or supply --dir.')
    sources = read_tsv(coverage)
    gaps = read_tsv(missing)
    sources.sort(key=lambda r: int(r['without_direct_hpoa']), reverse=True)
    with_xrefs = sum(int(r['xref_count']) > 0 for r in gaps)
    print('\n========== MONDO XREF SUMMARY ==========')
    print(f'MONDO concepts without direct HPOA: {len(gaps):,}')
    print(f'  With external xrefs: {with_xrefs:,}')
    print(f'  Without external xrefs: {len(gaps) - with_xrefs:,}')
    print(f'External source prefixes: {len(sources):,}')
    print('\nTop sources covering MONDO concepts without direct HPOA:')
    print(f'{"SOURCE":23} {"UNLINKED":>10} {"ALL MONDO":>12} {"LINKED":>10}')
    for row in sources[:args.top]:
        print(f'{row["source_prefix"][:23]:23} {int(row["without_direct_hpoa"]):>10,} '
              f'{int(row["mondo_concepts_with_xref"]):>12,} {int(row["with_direct_hpoa"]):>10,}')
    print('\nNote: Counts overlap across sources; xrefs do not guarantee phenotype data or exact equivalence.')


if __name__ == '__main__':
    main()
