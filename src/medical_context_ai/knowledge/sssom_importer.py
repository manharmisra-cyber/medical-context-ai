
import csv
from collections import defaultdict
from pathlib import Path

from .identity import normalize_external_id


def load_sssom_mappings(
    path: str | Path,
    known_mondo_ids: set[str],
) -> tuple[dict[str, str], dict[str, set[str]]]:
    """
    Load exact MONDO mappings from an SSSOM TSV.

    Returns:
        verified: External ID -> MONDO ID, where the
                  exact mapping is unique.
        conflicts: External ID -> multiple MONDO IDs.

    Only mappings to known MONDO concepts are accepted.
    """
    path = Path(path)
    exact_candidates = defaultdict(set)

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = (
            line for line in file
            if line.strip() and not line.startswith("#")
        )

        reader = csv.DictReader(rows, delimiter="\t")

        required = {"subject_id", "predicate_id", "object_id"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Invalid SSSOM mapping columns")

        for row in reader:
            if row["predicate_id"] != "skos:exactMatch":
                continue

            subject = row["subject_id"].strip()
            object_id = row["object_id"].strip()

            if subject.startswith("MONDO:"):
                mondo_id = subject
                external_id = object_id
            elif object_id.startswith("MONDO:"):
                mondo_id = object_id
                external_id = subject
            else:
                continue

            if mondo_id not in known_mondo_ids:
                continue

            external_id = normalize_external_id(external_id)

            if not external_id.startswith(("OMIM:", "ORPHA:")):
                continue

            exact_candidates[external_id].add(mondo_id)

    verified = {
        external_id: next(iter(mondo_ids))
        for external_id, mondo_ids in exact_candidates.items()
        if len(mondo_ids) == 1
    }

    conflicts = {
        external_id: mondo_ids
        for external_id, mondo_ids in exact_candidates.items()
        if len(mondo_ids) > 1
    }

    return verified, conflicts
