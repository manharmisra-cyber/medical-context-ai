from collections import defaultdict

from .schema import MedicalNode, MedicalEdge, EdgeType


class MedicalKnowledgeGraph:
    def __init__(self):
        self.nodes: dict[str, MedicalNode] = {}
        self.edges: list[MedicalEdge] = []
        self._outgoing: dict[str, list[MedicalEdge]] = defaultdict(list)
        self._incoming: dict[str, list[MedicalEdge]] = defaultdict(list)

    def add_node(self, node: MedicalNode) -> None:
        if not node.id or not node.label or not node.source:
            raise ValueError("Node ID, label and source are required")

        if node.id in self.nodes:
            raise ValueError(f"Duplicate node ID: {node.id}")

        self.nodes[node.id] = node

    def add_edge(self, edge: MedicalEdge) -> None:
        if edge.source_id not in self.nodes:
            raise ValueError(f"Unknown source node: {edge.source_id}")

        if edge.target_id not in self.nodes:
            raise ValueError(f"Unknown target node: {edge.target_id}")

        if not edge.provenance_id:
            raise ValueError("Every edge requires provenance")

        if edge in self.edges:
            raise ValueError("Duplicate edge")

        self.edges.append(edge)
        self._outgoing[edge.source_id].append(edge)
        self._incoming[edge.target_id].append(edge)

    def get_node(self, node_id: str) -> MedicalNode | None:
        return self.nodes.get(node_id)

    def neighbors(
        self,
        node_id: str,
        edge_type: EdgeType | None = None,
        direction: str = "outgoing",
    ) -> list[MedicalNode]:
        if node_id not in self.nodes:
            raise KeyError(f"Unknown node: {node_id}")

        if direction == "outgoing":
            edges = self._outgoing[node_id]
            get_id = lambda edge: edge.target_id
        elif direction == "incoming":
            edges = self._incoming[node_id]
            get_id = lambda edge: edge.source_id
        else:
            raise ValueError("Direction must be outgoing or incoming")

        return [
            self.nodes[get_id(edge)]
            for edge in edges
            if edge_type is None or edge.edge_type == edge_type
        ]

    def outgoing_edges(self, node_id: str) -> list[MedicalEdge]:
        if node_id not in self.nodes:
            raise KeyError(f"Unknown node: {node_id}")

        return list(self._outgoing[node_id])

    def __len__(self) -> int:
        return len(self.nodes)