from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    DISEASE = "disease"
    PHENOTYPE = "phenotype"
    SYMPTOM = "symptom"
    SIGN = "sign"
    TEST = "test"
    FINDING = "finding"
    GUIDELINE = "guideline"


class EdgeType(str, Enum):
    IS_A = "is_a"
    PART_OF = "part_of"
    ASSOCIATED_WITH = "associated_with"
    HAS_PHENOTYPE = "has_phenotype"
    REQUIRES_TEST = "requires_test"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"


@dataclass(frozen=True)
class MedicalNode:
    id: str
    label: str
    node_type: NodeType
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MedicalEdge:
    source_id: str
    target_id: str
    edge_type: EdgeType
    provenance_id: str
    metadata: dict[str, Any] = field(default_factory=dict)