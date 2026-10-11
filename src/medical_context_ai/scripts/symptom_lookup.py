
from medical_context_ai.scripts.medical_data import get_medical_data
from medical_context_ai.knowledge.hpo_terms import search_hpo_terms
from medical_context_ai.knowledge.identity import normalize_external_id
from medical_context_ai.reasoning.evidence import PatientEvidence
from medical_context_ai.reasoning.ranking import rank_diseases


def choose_term(query, terms):
    matches = search_hpo_terms(query, terms, limit=8)

    if not matches:
        print(f"No HPO term found for '{query}'.")
        return None

    # Automatically select an exact name, synonym, or ID match.
    normalized_query = query.strip().casefold()

    exact = [
        term for term in matches
        if normalized_query == term.id.casefold()
        or normalized_query == term.name.casefold()
        or any(
            normalized_query == synonym.casefold()
            for synonym in term.synonyms
        )
    ]

    if len(exact) == 1:
        term = exact[0]
        print(f"  {query} -> {term.name} ({term.id})")
        return term.id

    if len(matches) == 1:
        term = matches[0]
        print(f"  {query} -> {term.name} ({term.id})")
        return term.id

    print(f"\nMatches for '{query}':")

    for index, term in enumerate(matches, 1):
        print(f"  {index}. {term.name} [{term.id}]")

    choice = input("Select number (0 to skip): ").strip()

    if not choice.isdigit():
        return None

    number = int(choice)

    if not 1 <= number <= len(matches):
        return None

    return matches[number - 1].id


def resolve_findings(raw, terms):
    """Convert comma-separated symptom names into HPO IDs."""
    selected = set()

    for query in raw.split(","):
        query = query.strip()

        if not query:
            continue

        phenotype_id = choose_term(query, terms)

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
        mapping = f"Approved MONDO mapping: {approved}"

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
    graph, associations, terms, resolver = get_medical_data()

    print("\n========== SYMPTOM SEARCH ==========")
    print("Enter ALL symptoms separated by commas.")
    print("Example: fever, headache, seizures")

    raw = input("\nPresent findings: ").strip()

    selected = resolve_findings(raw, terms)

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

    absent = resolve_findings(absent_raw, terms)

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
