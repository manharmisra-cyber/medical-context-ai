
from .semantic_matcher import SemanticHPOMatcher


class InteractivePhenotypeResolver:
    def __init__(self, hpo_terms, matcher=None):
        self.hpo_terms = hpo_terms
        self.matcher = matcher

    def get_matcher(self):
        if self.matcher is None:
            self.matcher = SemanticHPOMatcher(self.hpo_terms)
        return self.matcher

    def resolve(self, phrase: str):
        phrase = phrase.strip()

        while phrase:
            results = self.get_matcher().search(
                phrase, top_k=5
            )

            if not results:
                print(f"No HPO candidates for '{phrase}'.")
                return None

            print(f"\nInterpretation of: '{phrase}'")
            print("-" * 55)

            for index, result in enumerate(results, 1):
                hpo_id = result["hpo_id"]
                term = self.hpo_terms.get(hpo_id)

                definition = (
                    getattr(term, "definition", None)
                    if term is not None else None
                )

                if isinstance(term, dict):
                    definition = term.get("definition")

                print(
                    f"\n{index}. {result['name']} [{hpo_id}]"
                )
                print(
                    f"   Similarity: "
                    f"{result['similarity']:.3f}"
                )

                if definition:
                    print(f"   Definition: {definition}")
                else:
                    print(
                        "   Definition unavailable in "
                        "loaded HPO terminology."
                    )

            print("\n0. None of these")

            choice = input(
                "\nSelect 0-5 or enter a new symptom: "
            ).strip()

            if choice == "0":
                return None

            if choice.isdigit():
                number = int(choice)

                if 1 <= number <= len(results):
                    selected = results[number - 1]
                    print(
                        f"Confirmed: {selected['name']} "
                        f"[{selected['hpo_id']}]"
                    )
                    return selected["hpo_id"]

                print("Invalid selection.")
                continue

            if choice:
                phrase = choice

        return None
