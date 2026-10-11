
from medical_context_ai.scripts.medical_data import get_medical_data
from medical_context_ai.knowledge.identity import normalize_external_id


def show_icd_search(disease_name):
    choice = input("\nSearch WHO ICD-11 for this disease? (y/n): ")
    if choice.strip().lower() != "y":
        return

    from medical_context_ai.knowledge.icd_client import ICDClient

    try:
        client = ICDClient()
        results = client.search(disease_name)

        entities = results.get("destinationEntities", [])

        print("\nWHO ICD-11 SEARCH RESULTS")
        print("These are search matches, not verified mappings.")

        for entity in entities[:5]:
            print(f"  {entity.get('title', 'Unknown')}")
            print(f"  {entity.get('id', 'No entity ID')}")
            print()

        if not entities:
            print("No WHO results found.")

    except Exception as error:
        print(f"WHO lookup failed: {error}")


def run_disease_lookup():
    graph, associations, terms, resolver = get_medical_data()

    query = input("\nDisease name or MONDO ID: ").strip()

    if not query:
        return

    matches = [
        node for node in graph.nodes.values()
        if query.casefold() in node.label.casefold()
        or query.upper() == node.id
    ]

    if not matches:
        print("No matching disease found.")
        return

    matches = matches[:15]

    print("\nMatching diseases:")
    for i, node in enumerate(matches, 1):
        print(f"{i}. {node.label} [{node.id}]")

    selection = input("\nSelect disease number (0 to cancel): ")

    if not selection.isdigit():
        return

    number = int(selection)

    if not 1 <= number <= len(matches):
        return

    node = matches[number - 1]

    print(f"\n========== {node.label.upper()} ==========")
    print(f"MONDO: {node.id}")
    print(f"Source: {node.source}")

    xrefs = node.metadata.get("xrefs", [])

    print("\nExternal identifiers:")
    for xref in xrefs[:20]:
        print(f"  {xref}")

    phenotype_ids = set()
    matched_sources = set()

    for disease_id, phenotypes in associations.items():
        normalized = normalize_external_id(disease_id)

        approved = resolver.resolve(normalized)
        candidates = resolver.candidates.get(normalized, set())

        # Display candidate associations, but don't claim
        # they are verified disease equivalences.
        if approved == node.id or node.id in candidates:
            phenotype_ids.update(phenotypes)
            matched_sources.add(disease_id)

    print("\nPotential associated phenotypes:")
    print("Based on MONDO cross-reference candidates; not all are exact.")

    for hp_id in sorted(phenotype_ids)[:40]:
        term = terms.get(hp_id)
        name = term.name if term else "Unknown phenotype"
        print(f"  {name} [{hp_id}]")

    print(f"\nTotal potential HPO terms: {len(phenotype_ids)}")
    print(f"HPO source disease IDs: {len(matched_sources)}")

    show_icd_search(node.label)


if __name__ == "__main__":
    run_disease_lookup()
