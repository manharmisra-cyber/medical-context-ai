
from functools import lru_cache
from pathlib import Path

from medical_context_ai.knowledge.mondo_importer import load_mondo
from medical_context_ai.knowledge.hpo_importer import load_hpo_associations
from medical_context_ai.knowledge.hpo_terms import load_hpo_terms
from medical_context_ai.knowledge.identity import build_identity_resolver


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "external"


@lru_cache(maxsize=1)
def get_medical_data():
    print("Loading MONDO, HPO associations and terminology...")

    graph = load_mondo(DATA / "mondo.json")
    associations = load_hpo_associations(DATA / "phenotype.hpoa")
    terms = load_hpo_terms(DATA / "hp.obo")
    resolver = build_identity_resolver(graph)

    print(
        f"Loaded {len(graph.nodes):,} MONDO concepts, "
        f"{len(associations):,} disease associations, "
        f"{len(terms):,} HPO terms."
    )

    return graph, associations, terms, resolver
