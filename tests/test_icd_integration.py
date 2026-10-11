
import unittest
from unittest.mock import Mock

from medical_context_ai.knowledge.identity import IdentityResolver
from medical_context_ai.knowledge.icd_integration import (
    ICDIntegration,
)


class TestICDIntegration(unittest.TestCase):

    def test_verified_mapping(self):
        resolver = IdentityResolver(
            known_mondo_ids={"MONDO:0000001"}
        )

        uri = "http://id.who.int/icd/entity/123456"

        resolver.approve_icd_mapping(
            "MONDO:0000001",
            uri,
        )

        mock_client = Mock()
        mock_client.get_entity.return_value = {
            "@id": uri,
            "title": {"@value": "Synthetic disease"},
        }

        integration = ICDIntegration(
            resolver,
            client=mock_client,
        )

        result = integration.fetch_entity("123456")

        self.assertEqual(result.mondo_id, "MONDO:0000001")
        self.assertEqual(result.title, "Synthetic disease")

    def test_unmapped_entity(self):
        resolver = IdentityResolver()

        mock_client = Mock()
        mock_client.get_entity.return_value = {
            "@id": "http://id.who.int/icd/entity/999999",
            "title": {"@value": "Unmapped disease"},
        }

        integration = ICDIntegration(
            resolver,
            client=mock_client,
        )

        result = integration.fetch_entity("999999")

        self.assertIsNone(result.mondo_id)


if __name__ == "__main__":
    unittest.main()
