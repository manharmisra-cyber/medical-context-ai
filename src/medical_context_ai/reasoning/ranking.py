
from dataclasses import dataclass

from .evidence import PatientEvidence


@dataclass
class RankedDisease:
    disease_id: str
    score: float
    matched_phenotypes: set[str]
    missing_phenotypes: set[str]
    coverage: float
    classification: str


def rank_diseases(
    evidence: PatientEvidence,
    associations: dict[str, set[str]],
    weights: dict[str, float] | None = None,
) -> list[RankedDisease]:

    weights = weights or {}
    requested = evidence.present_phenotypes

    if not requested:
        return []

    results = []

    for disease_id, disease_phenotypes in associations.items():

        matched = requested & disease_phenotypes
        matched_count = len(matched)
        total_count = len(requested)

        coverage = matched_count / total_count

        if coverage == 1.0:
            classification = "MATCH"

        elif coverage > 0.5:
            classification = "PARTIAL MATCH"

        else:
            # Ignore diseases matching 50% or fewer findings
            continue

        absent_conflicts = (
            evidence.absent_phenotypes & disease_phenotypes
        )

        score = sum(
            weights.get(phenotype, 1.0)
            for phenotype in matched
        )

        score -= sum(
            weights.get(phenotype, 1.0)
            for phenotype in absent_conflicts
        )

        results.append(
            RankedDisease(
                disease_id=disease_id,
                score=score,
                matched_phenotypes=matched,
                missing_phenotypes=absent_conflicts,
                coverage=coverage,
                classification=classification,
            )
        )

    return sorted(
        results,
        key=lambda result: (
            -result.coverage,
            -result.score,
            result.disease_id,
        ),
    )
