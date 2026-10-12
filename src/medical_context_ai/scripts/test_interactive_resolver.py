
from pathlib import Path

from medical_context_ai.knowledge.hpo_terms import load_hpo_terms
from medical_context_ai.terminology.interactive_resolver import (
    InteractivePhenotypeResolver,
)


ROOT = Path(__file__).resolve().parents[3]

terms = load_hpo_terms(
    ROOT / "data" / "external" / "hp.obo"
)

resolver = InteractivePhenotypeResolver(terms)

while True:
    phrase = input(
        "\nEnter a symptom (or 'exit'): "
    ).strip()

    if phrase.lower() == "exit":
        break

    hpo_id = resolver.resolve(phrase)

    if hpo_id:
        print(f"Resolved HPO ID: {hpo_id}")
