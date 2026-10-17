"""Inspect BODHI-S CSV schemas, association edges, and MONDO xref metadata.

Read-only reconnaissance before writing a clinical-association importer.
Run: python -m medical_context_ai.scripts.inspect_bodhi_edges
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from medical_context_ai.scripts.medical_data import get_medical_data


def inspect_csv(path: Path, sample_size: int = 3) -> None:
    print(f"\n--- {path.name} ---")
    if not path.is_file():
        print(f"MISSING: {path}")
        return
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        print("Columns:", ", ".join(reader.fieldnames or []) or "(none)")
        examples = []
        count = 0
        for row in reader:
            count += 1
            if len(examples) < sample_size:
                examples.append(row)
        print(f"Rows: {count:,}")
        for i, example in enumerate(examples, 1):
            print(f"Sample {i}:")
            for key, value in example.items():
                short = str(value).replace("\n", " ")
                print(f"  {key}: {short[:180]}")


def inspect_mondo() -> None:
    print("\n--- MONDO SCTID mapping metadata ---")
    graph, associations, _, resolver = get_medical_data()
    linked = {
        resolved for disease_id in associations
        if (resolved := resolver.resolve(disease_id)) is not None
    }
    print(f"MONDO concepts: {len(graph.nodes):,}; with direct HPOA links: {len(linked):,}")
    samples = 0
    metadata_keys = Counter()
    xref_types = Counter()
    for mid, node in graph.nodes.items():
        meta = getattr(node, "metadata", {}) or {}
        metadata_keys.update(meta.keys())
        xrefs = meta.get("xrefs", []) or []
        if isinstance(xrefs, str):
            xrefs = [xrefs]
        for xref in xrefs:
            if str(xref).upper().startswith(("SCTID:", "SNOMED:")):
                xref_types[type(xref).__name__] += 1
                if samples < 5:
                    print(f"  {mid} | {node.label} | xref={xref!r} | metadata={str(meta)[:500]}")
                    samples += 1
    print("Metadata keys:", metadata_keys.most_common(20))
    print("SCTID xref representation:", dict(xref_types))
    print("Note: plain xref strings do not establish exact equivalence; predicate evidence may require MONDO SSSOM or source ontology metadata.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("data/external/bodhi-s/csv"))
    parser.add_argument("--samples", type=int, default=2)
    args = parser.parse_args()
    for filename in ("nodes_condition.csv", "nodes_symptom.csv", "edges_present_in.csv"):
        inspect_csv(args.directory / filename, max(0, args.samples))
    inspect_mondo()
    print("\nNext: use the actual column names and edge directions to implement a provenance-preserving BODHI importer.")


if __name__ == "__main__":
    main()
