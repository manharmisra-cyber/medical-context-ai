
from functools import lru_cache
from pathlib import Path

from medical_context_ai.knowledge.mondo_importer import load_mondo
from medical_context_ai.knowledge.hpo_importer import load_hpo_associations
from medical_context_ai.knowledge.hpo_terms import load_hpo_terms
from medical_context_ai.knowledge.identity import build_identity_resolver
from medical_context_ai.knowledge.sssom_importer import load_sssom_mappings


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "external"


@lru_cache(maxsize=1)
def get_medical_data():
    print("Loading MONDO, HPO associations and terminology...")

    # Load medical databases
    graph = load_mondo(DATA / "mondo.json")
    associations = load_hpo_associations(DATA / "phenotype.hpoa")
    terms = load_hpo_terms(DATA / "hp.obo")

    # Build identity resolver using the actual MONDO graph
    resolver = build_identity_resolver(graph)

    # Load authoritative SSSOM exact mappings
    verified, conflicts = load_sssom_mappings(
        DATA / "mondo.sssom.tsv",
        resolver.known_mondo_ids,
    )

    resolver.mappings.update(verified)

    print(
        f"Loaded {len(graph.nodes):,} MONDO concepts, "
        f"{len(associations):,} HPO disease associations, "
        f"{len(terms):,} HPO terms."
    )

    print(
        f"SSSOM exact mappings: {len(verified):,}, "
        f"conflicts: {len(conflicts):,}"
    )

    return graph, associations, terms, resolver
