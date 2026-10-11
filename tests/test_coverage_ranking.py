
import unittest

from medical_context_ai.reasoning.evidence import PatientEvidence
from medical_context_ai.reasoning.ranking import rank_diseases


class TestCoverageRanking(unittest.TestCase):

    def test_four_symptoms(self):
        evidence = PatientEvidence(
            present_phenotypes={"HP:1", "HP:2", "HP:3", "HP:4"}
        )

        associations = {
            "FULL": {"HP:1", "HP:2", "HP:3", "HP:4"},
            "PARTIAL": {"HP:1", "HP:2", "HP:3"},
            "HALF": {"HP:1", "HP:2"},
            "LOW": {"HP:1"},
            "NONE": {"HP:9"},
        }

        results = rank_diseases(evidence, associations)

        self.assertEqual(
            [r.disease_id for r in results],
            ["FULL", "PARTIAL"],
        )

        self.assertEqual(results[0].classification, "MATCH")
        self.assertEqual(results[1].classification, "PARTIAL MATCH")

        self.assertEqual(results[0].coverage, 1.0)
        self.assertEqual(results[1].coverage, 0.75)

    def test_two_symptoms(self):
        evidence = PatientEvidence(
            present_phenotypes={"HP:1", "HP:2"}
        )

        associations = {
            "FULL": {"HP:1", "HP:2"},
            "HALF": {"HP:1"},
        }

        results = rank_diseases(evidence, associations)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].disease_id, "FULL")

    def test_empty_evidence(self):
        evidence = PatientEvidence()
        self.assertEqual(rank_diseases(evidence, {}), [])


if __name__ == "__main__":
    unittest.main()
