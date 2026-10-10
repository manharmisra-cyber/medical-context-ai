
import csv
from collections import defaultdict
from pathlib import Path


def load_hpo_associations(file_path: str | Path):
    """
    Read phenotype.hpoa.

    Returns:
        dict[disease_id, set[phenotype_id]]

    Only positive phenotype associations are included.
    """

    associations = defaultdict(set)

    with Path(file_path).open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:

        lines = (
            line for line in file
            if line.strip() and not line.startswith("#")
        )

        reader = csv.DictReader(lines, delimiter="\t")

        required = {"database_id", "hpo_id"}

        if not required.issubset(reader.fieldnames or []):
            raise ValueError(
                f"Unexpected HPO columns: {reader.fieldnames}"
            )

        for row in reader:
            disease_id = row["database_id"].strip()
            phenotype_id = row["hpo_id"].strip()

            qualifier = row.get("qualifier", "").strip()

            # NOT associations mean the phenotype is explicitly absent.
            if qualifier == "NOT":
                continue

            if disease_id and phenotype_id:
                associations[disease_id].add(phenotype_id)

    return dict(associations)
