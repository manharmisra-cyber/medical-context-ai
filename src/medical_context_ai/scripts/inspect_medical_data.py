
import json
from pathlib import Path

from medical_context_ai.knowledge.hpo_importer import (
    load_hpo_associations,
)


ROOT = Path(__file__).resolve().parents[3]

MONDO_PATH = ROOT / "data" / "external" / "mondo.json"
HPO_PATH = ROOT / "data" / "external" / "phenotype.hpoa"


def main():
    print("MEDICAL CONTEXT AI - DATA INSPECTION")
    print("=" * 45)

    with MONDO_PATH.open("r", encoding="utf-8") as file:
        mondo = json.load(file)

    graphs = mondo.get("graphs", [])

    mondo_nodes = [
        node
        for graph in graphs
        for node in graph.get("nodes", [])
        if node.get("type") == "CLASS"
        and "MONDO_" in node.get("id", "")
    ]

    print(f"MONDO disease concepts: {len(mondo_nodes):,}")

    associations = load_hpo_associations(HPO_PATH)

    total_links = sum(
        len(phenotypes)
        for phenotypes in associations.values()
    )

    print(f"HPO annotated diseases: {len(associations):,}")
    print(f"HPO positive associations: {total_links:,}")

    print("\nSample HPO disease associations:")

    for disease_id, phenotypes in list(associations.items())[:5]:
        print(
            f"  {disease_id}: "
            f"{len(phenotypes)} phenotypes"
        )


if __name__ == "__main__":
    main()
