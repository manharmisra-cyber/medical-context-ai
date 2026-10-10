import unittest

from medical_context_ai.knowledge.schema import (
    MedicalNode,
    MedicalEdge,
    NodeType,
    EdgeType,
)

from medical_context_ai.knowledge.graph import MedicalKnowledgeGraph


class TestMedicalKnowledgeGraph(unittest.TestCase):
    def setUp(self):
        self.graph = MedicalKnowledgeGraph()

        self.disease = MedicalNode(
            id="MONDO:0000001",
            label="Example disease",
            node_type=NodeType.DISEASE,
            source="synthetic-test",
        )

        self.phenotype = MedicalNode(
            id="HP:0001945",
            label="Fever",
            node_type=NodeType.PHENOTYPE,
            source="synthetic-test",
        )

        self.graph.add_node(self.disease)
        self.graph.add_node(self.phenotype)

    def test_nodes_added(self):
        self.assertEqual(len(self.graph), 2)

    def test_duplicate_node_rejected(self):
        with self.assertRaises(ValueError):
            self.graph.add_node(self.disease)

    def test_edge_and_traversal(self):
        edge = MedicalEdge(
            source_id=self.disease.id,
            target_id=self.phenotype.id,
            edge_type=EdgeType.HAS_PHENOTYPE,
            provenance_id="synthetic:test-001",
        )

        self.graph.add_edge(edge)

        neighbors = self.graph.neighbors(
            self.disease.id,
            edge_type=EdgeType.HAS_PHENOTYPE,
        )

        self.assertEqual(neighbors, [self.phenotype])

    def test_unknown_node_edge_rejected(self):
        edge = MedicalEdge(
            source_id="MONDO:DOES_NOT_EXIST",
            target_id=self.phenotype.id,
            edge_type=EdgeType.HAS_PHENOTYPE,
            provenance_id="synthetic:test-002",
        )

        with self.assertRaises(ValueError):
            self.graph.add_edge(edge)

    def test_missing_provenance_rejected(self):
        edge = MedicalEdge(
            source_id=self.disease.id,
            target_id=self.phenotype.id,
            edge_type=EdgeType.HAS_PHENOTYPE,
            provenance_id="",
        )

        with self.assertRaises(ValueError):
            self.graph.add_edge(edge)


if __name__ == "__main__":
    unittest.main()