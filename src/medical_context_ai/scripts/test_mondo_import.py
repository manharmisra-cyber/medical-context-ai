
from pathlib import Path

from medical_context_ai.knowledge.mondo_importer import load_mondo


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MONDO_FILE = PROJECT_ROOT / "data" / "external" / "mondo.json"


def main():
    print("MEDICAL CONTEXT AI - MONDO IMPORT")
    print("=" * 45)

    graph = load_mondo(MONDO_FILE)

    print(f"Disease nodes: {len(graph.nodes):,}")
    print(f"IS_A relationships: {len(graph.edges):,}")

    print("\nSample diseases:")

    for node in list(graph.nodes.values())[:10]:
        print(f"{node.id}: {node.label}")

    print("\nSample external identifiers:")

    examples = [
        node for node in graph.nodes.values()
        if node.metadata.get("xrefs")
    ]

    for node in examples[:5]:
        print(f"{node.id}: {node.metadata['xrefs'][:5]}")


if __name__ == "__main__":
    main()
