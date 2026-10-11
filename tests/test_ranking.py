
import unittest

from medical_context_ai.reasoning.evidence import PatientEvidence
from medical_context_ai.reasoning.ranking import rank_diseases


class TestRanking(unittest.TestCase):

    def test_weighted_ranking(self):
        associations = {
            "OMIM:111111": {"HP:0001", "HP:0002"},
            "OMIM:222222": {"HP:0001"},
        }

        evidence = PatientEvidence(
            present_phenotypes={"HP:0001", "HP:0002"}
        )

        weights = {
            "HP:0001": 1.0,
            "HP:0002": 3.0,
        }

        results = rank_diseases(
            evidence,
            associations,
            weights,
        )

        self.assertEqual(results[0].disease_id, "OMIM:111111")
        self.assertEqual(results[0].score, 4.0)

    def test_negative_evidence(self):
        associations = {
            "OMIM:111111": {"HP:0001", "HP:0002"}
        }

        evidence = PatientEvidence(
            present_phenotypes={"HP:0001"},
            absent_phenotypes={"HP:0002"},
        )

        results = rank_diseases(evidence, associations)

        self.assertEqual(results[0].score, 0.0)

    def test_contradictory_evidence(self):
        with self.assertRaises(ValueError):
            PatientEvidence(
                present_phenotypes={"HP:0001"},
                absent_phenotypes={"HP:0001"},
            )


if __name__ == "__main__":
    unittest.main()
