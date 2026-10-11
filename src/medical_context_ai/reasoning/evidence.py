
from dataclasses import dataclass, field


@dataclass
class PatientEvidence:
    present_phenotypes: set[str] = field(default_factory=set)
    absent_phenotypes: set[str] = field(default_factory=set)

    def __post_init__(self):
        overlap = (
            self.present_phenotypes
            & self.absent_phenotypes
        )

        if overlap:
            raise ValueError(
                f"Contradictory patient evidence: {overlap}"
            )
