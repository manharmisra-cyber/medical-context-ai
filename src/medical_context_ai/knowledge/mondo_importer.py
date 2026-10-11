
import json
from pathlib import Path

from .graph import MedicalKnowledgeGraph
from .schema import MedicalNode, MedicalEdge, NodeType, EdgeType


MONDO_PREFIX = "http://purl.obolibrary.org/obo/MONDO_"


def normalize_mondo_id(value: str) -> str | None:
    if value.startswith(MONDO_PREFIX):
        suffix = value[len(MONDO_PREFIX):]
        if suffix.isdigit():
            return f"MONDO:{suffix}"

    if value.startswith("MONDO:"):
        return value

    return None


def load_mondo(file_path: str | Path) -> MedicalKnowledgeGraph:
    file_path = Path(file_path)

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    kg = MedicalKnowledgeGraph()

    # First pass: disease concepts
    for ontology in data.get("graphs", []):
        for item in ontology.get("nodes", []):
            identifier = normalize_mondo_id(item.get("id", ""))

            if not identifier:
                continue

            if item.get("type") != "CLASS":
                continue

            if not item.get("lbl"):
                continue

            if item.get("meta", {}).get("deprecated", False):
                continue

            if identifier in kg.nodes:
                continue

            kg.add_node(
                MedicalNode(
                    id=identifier,
                    label=item["lbl"],
                    node_type=NodeType.DISEASE,
                    source="MONDO",
                    metadata={
                        "original_id": item["id"],
                        "xrefs": [
                            x.get("val")
                            for x in item.get("meta", {}).get("xrefs", [])
                            if x.get("val")
                        ],
                    },
                )
            )

    # Second pass: disease hierarchy
    for ontology in data.get("graphs", []):
        for relation in ontology.get("edges", []):
            if relation.get("pred") != "is_a":
                continue

            child = normalize_mondo_id(relation.get("sub", ""))
            parent = normalize_mondo_id(relation.get("obj", ""))

            if child not in kg.nodes or parent not in kg.nodes:
                continue

            kg.add_edge(
                MedicalEdge(
                    source_id=child,
                    target_id=parent,
                    edge_type=EdgeType.IS_A,
                    provenance_id="MONDO:ontology-import",
                )
            )

    return kg
