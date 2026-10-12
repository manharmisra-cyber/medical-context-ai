
from pathlib import Path

from medical_context_ai.knowledge.hpo_terms import (
    load_hpo_terms,
)
from medical_context_ai.terminology.semantic_matcher import (
    SemanticHPOMatcher,
)


ROOT = Path(__file__).resolve().parents[3]

terms = load_hpo_terms(
    ROOT / "data" / "external" / "hp.obo"
)

matcher = SemanticHPOMatcher(terms)

queries = [
    "fever",
    "high temperature",
    "my head hurts",
    "feeling hot",
    "difficulty breathing",
    "pain in my chest",
]

for query in queries:
    print(f"\nQUERY: {query}")

    for result in matcher.search(query):
        print(
            f"  {result['hpo_id']} "
            f"{result['name']} "
            f"(similarity={result['similarity']}) "
            f"[matched: {result['matched_phrase']}]"
        )
