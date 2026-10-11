
from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class HPOTerm:
    id: str
    name: str
    synonyms: set[str] = field(default_factory=set)


def load_hpo_terms(path: str | Path) -> dict[str, HPOTerm]:
    """Read HPO names and synonyms from an OBO file."""
    terms = {}
    current = {}
    in_term = False

    def save_term():
        if (
            current.get("id", "").startswith("HP:")
            and current.get("name")
            and not current.get("obsolete")
        ):
            terms[current["id"]] = HPOTerm(
                id=current["id"],
                name=current["name"],
                synonyms=set(current.get("synonyms", [])),
            )

    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line == "[Term]":
                save_term()
                current = {}
                in_term = True
                continue

            if line.startswith("[") and line.endswith("]"):
                save_term()
                current = {}
                in_term = False
                continue

            if not in_term:
                continue

            if line.startswith("id: "):
                current["id"] = line[4:]

            elif line.startswith("name: "):
                current["name"] = line[6:]

            elif line.startswith("synonym: "):
                match = re.search(r'^synonym: "((?:[^"\\]|\\.)*)"', line)
                if match:
                    current.setdefault("synonyms", []).append(
                        match.group(1).replace('\\"', '"')
                    )

            elif line == "is_obsolete: true":
                current["obsolete"] = True

    save_term()
    return terms


def search_hpo_terms(
    query: str,
    terms: dict[str, HPOTerm],
    limit: int = 10,
) -> list[HPOTerm]:
    query = query.strip().casefold()

    if not query:
        return []

    exact = []
    partial = []

    for term in terms.values():
        names = [term.name, *term.synonyms]
        normalized = [name.casefold() for name in names]

        if query == term.id.casefold() or query in normalized:
            exact.append(term)
        elif any(query in name for name in normalized):
            partial.append(term)

    return (
        sorted(exact, key=lambda t: t.name)
        + sorted(partial, key=lambda t: t.name)
    )[:limit]
