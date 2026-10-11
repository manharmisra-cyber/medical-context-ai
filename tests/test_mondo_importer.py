
import json
import tempfile
import unittest
from pathlib import Path

from medical_context_ai.knowledge.mondo_importer import (
    load_mondo,
    normalize_mondo_id,
)


class TestMondoImporter(unittest.TestCase):

    def test_normalization(self):
        self.assertEqual(
            normalize_mondo_id(
                "http://purl.obolibrary.org/obo/MONDO_0000001"
            ),
            "MONDO:0000001",
        )

    def test_import(self):
        sample = {
            "graphs": [{
                "nodes": [
                    {
                        "id": "http://purl.obolibrary.org/obo/MONDO_0000001",
                        "lbl": "Synthetic disease A",
                        "type": "CLASS",
                        "meta": {"xrefs": [{"val": "OMIM:123456"}]},
                    },
                    {
                        "id": "http://purl.obolibrary.org/obo/MONDO_0000002",
                        "lbl": "Synthetic disease B",
                        "type": "CLASS",
                    },
                ],
                "edges": [{
                    "sub": "http://purl.obolibrary.org/obo/MONDO_0000002",
                    "pred": "is_a",
                    "obj": "http://purl.obolibrary.org/obo/MONDO_0000001",
                }],
            }]
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mondo.json"
            path.write_text(json.dumps(sample), encoding="utf-8")
            graph = load_mondo(path)

        self.assertEqual(len(graph.nodes), 2)
        self.assertEqual(len(graph.edges), 1)

        self.assertEqual(
            graph.nodes["MONDO:0000001"].metadata["xrefs"],
            ["OMIM:123456"],
        )


if __name__ == "__main__":
    unittest.main()
