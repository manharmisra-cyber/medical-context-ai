
from dataclasses import dataclass

from medical_context_ai.scripts.medical_data import (
    get_medical_data,
)
from medical_context_ai.terminology.semantic_matcher import (
    SemanticHPOMatcher,
)


@dataclass
class MedicalRuntime:
    graph: object
    associations: dict
    terms: dict
    identity_resolver: object
    semantic_matcher: SemanticHPOMatcher


_runtime = None


def initialize_runtime():
    global _runtime

    if _runtime is not None:
        return _runtime

    print("\nInitializing Medical Context AI...")

    graph, associations, terms, resolver = (
        get_medical_data()
    )

    matcher = SemanticHPOMatcher(
        terms,
        cache_dir="data/cache",
    )

    _runtime = MedicalRuntime(
        graph=graph,
        associations=associations,
        terms=terms,
        identity_resolver=resolver,
        semantic_matcher=matcher,
    )

    print("\nMedical Context AI READY.")

    return _runtime
