
from pathlib import Path

from medical_context_ai.knowledge.mondo_importer import load_mondo
from medical_context_ai.knowledge.hpo_importer import (
    load_hpo_associations,
)
from medical_context_ai.knowledge.identity import (
    build_identity_resolver,
    normalize_external_id,
)


ROOT = Path(__file__).resolve().parents[3]

MONDO_PATH = ROOT / "data" / "external" / "mondo.json"
HPO_PATH = ROOT / "data" / "external" / "phenotype.hpoa"


def main():
    print("MEDICAL CONTEXT AI - IDENTITY INTEGRATION")
    print("=" * 48)

    graph = load_mondo(MONDO_PATH)
    associations = load_hpo_associations(HPO_PATH)
    resolver = build_identity_resolver(graph)

    single = 0
    multiple = 0
    missing = 0

    examples = []

    for disease_id in associations:
        external_id = normalize_external_id(disease_id)
        matches = resolver.ambiguous.get(external_id, set())

        if len(matches) == 1:
            single += 1

            if len(examples) < 10:
                examples.append((disease_id, next(iter(matches))))

        elif len(matches) > 1:
            multiple += 1

        else:
            missing += 1

    print(f"MONDO nodes: {len(graph.nodes):,}")
    print(f"HPO disease IDs: {len(associations):,}")

    print(f"Single candidates: {single:,}")
    print(f"Multiple candidates: {multiple:,}")
    print(f"Unmatched: {missing:,}")

    print("\nCandidate mappings:")

    for external_id, mondo_id in examples:
        print(f"{external_id} -> {mondo_id}")

    print("\nNo candidate mappings automatically approved.")


if __name__ == "__main__":
    main()
