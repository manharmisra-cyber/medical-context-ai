
from dataclasses import dataclass

from .evidence import PatientEvidence


@dataclass
class RankedDisease:
    disease_id: str
    score: float
    matched_phenotypes: set[str]
    missing_phenotypes: set[str]


def rank_diseases(
    evidence: PatientEvidence,
    associations: dict[str, set[str]],
    weights: dict[str, float] | None = None,
) -> list[RankedDisease]:
    """
    Prototype ranking based on HPO associations.

    Scores are heuristic and NOT disease probabilities.
    """
    weights = weights or {}
    results = []

    for disease_id, phenotypes in associations.items():
        matched = evidence.present_phenotypes & phenotypes
        missing = evidence.absent_phenotypes & phenotypes

        if not matched:
            continue

        positive_score = sum(
            weights.get(phenotype, 1.0)
            for phenotype in matched
        )

        negative_score = sum(
            weights.get(phenotype, 1.0)
            for phenotype in missing
        )

        score = positive_score - negative_score

        results.append(
            RankedDisease(
                disease_id=disease_id,
                score=score,
                matched_phenotypes=matched,
                missing_phenotypes=missing,
            )
        )

    return sorted(
        results,
        key=lambda result: (-result.score, result.disease_id),
    )
