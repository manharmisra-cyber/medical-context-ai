
from medical_context_ai.scripts.runtime import initialize_runtime
from medical_context_ai.knowledge.identity import normalize_external_id
from medical_context_ai.reasoning.evidence import PatientEvidence
from medical_context_ai.reasoning.ranking import rank_diseases


def choose_term(query, terms, matcher):
    """Ask the user to confirm an HPO concept suggested by SapBERT."""
    while query:
        results = matcher.search(query, top_k=5)
        if not results:
            print(f"No HPO candidates found for {query!r}.")
            return None

        print(f"\nInterpretation of: {query!r}")
        print("-" * 55)
        for index, result in enumerate(results, 1):
            hpo_id = result["hpo_id"]
            term = terms.get(hpo_id)
            definition = (
                term.get("definition") if isinstance(term, dict)
                else getattr(term, "definition", None)
            ) if term is not None else None
            print(f"{index}. {result['name']} [{hpo_id}] "
                  f"(similarity: {result['similarity']:.3f})")
            if definition:
                print(f"   Definition: {definition}")
            else:
                print("   Definition unavailable in loaded HPO data.")
        print("0. None of these")

        while True:
            choice = input("Select 0-5, or type a new symptom: ").strip()
            if choice == "0":
                return None
            if choice.isdigit():
                number = int(choice)
                if 1 <= number <= len(results):
                    selected = results[number - 1]
                    print(f"Confirmed: {selected['name']} [{selected['hpo_id']}]")
                    return selected["hpo_id"]
                print("Invalid selection. Choose one of the displayed numbers.")
            elif choice:
                query = choice
                break
            else:
                print("Enter a number or a symptom.")
    return None


def resolve_findings(raw, terms, matcher):
    """Convert comma-separated phrases into user-confirmed HPO IDs."""
    selected = set()
    for query in raw.split(","):
        query = query.strip()
        if query:
            phenotype_id = choose_term(query, terms, matcher)
            if phenotype_id:
                selected.add(phenotype_id)
    return selected


def get_disease_identity(result, graph, resolver):
    external_id = normalize_external_id(result.disease_id)

    approved = resolver.resolve(external_id)
    candidates = resolver.candidates.get(external_id, set())

    if approved:
        node = graph.get_node(approved)
        name = node.label if node else external_id
        mapping = f"MONDO exact/approved mapping: {approved}"

    elif len(candidates) == 1:
        mondo_id = next(iter(candidates))
        node = graph.get_node(mondo_id)

        name = node.label if node else external_id
        mapping = f"Unverified MONDO candidate: {mondo_id}"

    elif len(candidates) > 1:
        name = external_id
        mapping = f"{len(candidates)} possible MONDO mappings"

    else:
        name = external_id
        mapping = "No MONDO mapping"

    return name, mapping


def display_result(index, result, graph, resolver, terms, total):
    name, mapping = get_disease_identity(result, graph, resolver)

    matched_names = [
        terms[hp].name if hp in terms else hp
        for hp in sorted(result.matched_phenotypes)
    ]

    unmatched = (
        result.requested_phenotypes
        if hasattr(result, "requested_phenotypes")
        else None
    )

    print(f"\n{index}. {name}")
    print(f"   Classification: {result.classification}")
    print(f"   Source ID: {result.disease_id}")
    print(f"   Coverage: {result.coverage:.1%}")
    print(f"   Matched: {len(result.matched_phenotypes)}/{total}")
    print(f"   Heuristic score: {result.score:.2f}")
    print(f"   Mapping: {mapping}")
    print(f"   Supporting findings: {', '.join(matched_names)}")


def run_symptom_lookup():
    runtime = initialize_runtime()
    graph, associations, terms, resolver = (
        runtime.graph, runtime.associations, runtime.terms, runtime.identity_resolver
    )

    print("\n========== SYMPTOM SEARCH ==========")
    print("Enter ALL symptoms separated by commas.")
    print("Example: fever, headache, seizures")

    raw = input("\nPresent findings: ").strip()

    selected = resolve_findings(raw, terms, runtime.semantic_matcher)

    if not selected:
        print("No recognized findings selected.")
        return

    print("\nSelected findings:")

    for hp_id in sorted(selected):
        name = terms[hp_id].name if hp_id in terms else hp_id
        print(f"  - {name} [{hp_id}]")

    absent_raw = input(
        "\nConfirmed absent findings (optional, comma-separated): "
    ).strip()

    absent = resolve_findings(absent_raw, terms, runtime.semantic_matcher)

    if selected & absent:
        print("\nERROR: A finding cannot be both present and absent.")
        return

    evidence = PatientEvidence(
        present_phenotypes=selected,
        absent_phenotypes=absent,
    )

    # All symptoms are evaluated TOGETHER in one ranking call.
    results = rank_diseases(evidence, associations)

    full_matches = [
        result for result in results
        if result.classification == "MATCH"
    ]

    partial_matches = [
        result for result in results
        if result.classification == "PARTIAL MATCH"
    ]

    print("\n" + "=" * 55)
    print("                 HYPOTHESIS RESULTS")
    print("=" * 55)

    print(f"\nTotal findings: {len(selected)}")
    print(f"Full matches: {len(full_matches)}")
    print(f"Partial matches: {len(partial_matches)}")

    print("\nRules:")
    print("  MATCH         = 100% of findings annotated")
    print("  PARTIAL MATCH = >50% but <100% annotated")
    print("  IRRELEVANT    = <=50% annotated (hidden)")
    print("\nThese are annotation matches, NOT diagnoses.")

    print("\n========== FULL MATCHES ==========")

    if not full_matches:
        print("No diseases have all selected findings annotated.")

    for index, result in enumerate(full_matches[:20], 1):
        display_result(
            index, result, graph, resolver, terms, len(selected)
        )

    print("\n========== PARTIAL MATCHES ==========")

    if not partial_matches:
        print("No diseases matched more than half the findings.")

    for index, result in enumerate(partial_matches[:20], 1):
        display_result(
            index, result, graph, resolver, terms, len(selected)
        )

    print("\n" + "=" * 55)
    print("Search complete.")
    print(
        "Warning: HPO annotations are incomplete. "
        "Filtered diseases are not medically ruled out."
    )


if __name__ == "__main__":
    run_symptom_lookup()
