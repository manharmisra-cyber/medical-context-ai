
from collections import defaultdict
from dataclasses import dataclass, field

from .graph import MedicalKnowledgeGraph


ICD_PREFIX = "http://id.who.int/icd/entity/"


def normalize_external_id(identifier: str) -> str:
    identifier = identifier.strip()

    if identifier.startswith(("http://", "https://")):
        return identifier

    if ":" not in identifier:
        return identifier

    prefix, value = identifier.split(":", 1)

    aliases = {
        "ORPHANET": "ORPHA",
        "ORPHA": "ORPHA",
        "OMIM": "OMIM",
        "MONDO": "MONDO",
    }

    return f"{aliases.get(prefix.upper(), prefix.upper())}:{value}"


@dataclass
class IdentityResolver:
    mappings: dict[str, str] = field(default_factory=dict)
    candidates: dict[str, set[str]] = field(default_factory=dict)
    known_mondo_ids: set[str] = field(default_factory=set)

    @property
    def ambiguous(self) -> dict[str, set[str]]:
        """Compatibility with the earlier integration script."""
        return self.candidates

    def resolve(self, identifier: str) -> str | None:
        identifier = normalize_external_id(identifier)

        if identifier.startswith("MONDO:"):
            return identifier if identifier in self.known_mondo_ids else None

        return self.mappings.get(identifier)

    def approve_mapping(
        self,
        external_id: str,
        mondo_id: str,
    ) -> None:
        external_id = normalize_external_id(external_id)

        if mondo_id not in self.known_mondo_ids:
            raise ValueError(f"Unknown MONDO ID: {mondo_id}")

        existing = self.mappings.get(external_id)

        if existing is not None and existing != mondo_id:
            raise ValueError("Conflicting approved mapping")

        candidates = self.candidates.get(external_id)

        if candidates is not None and mondo_id not in candidates:
            raise ValueError("MONDO ID is not a recorded candidate")

        self.mappings[external_id] = mondo_id

    def approve_icd_mapping(
        self,
        mondo_id: str,
        icd_entity_uri: str,
    ) -> None:
        if not icd_entity_uri.startswith(ICD_PREFIX):
            raise ValueError("Expected WHO Foundation entity URI")

        entity_number = icd_entity_uri[len(ICD_PREFIX):]

        if not entity_number.isdigit():
            raise ValueError("Invalid WHO Foundation entity ID")

        self.approve_mapping(icd_entity_uri, mondo_id)


def build_identity_resolver(
    graph: MedicalKnowledgeGraph,
) -> IdentityResolver:
    candidates = defaultdict(set)

    for node in graph.nodes.values():
        for xref in node.metadata.get("xrefs", []):
            external_id = normalize_external_id(xref)

            if external_id.startswith(("OMIM:", "ORPHA:")):
                candidates[external_id].add(node.id)

    return IdentityResolver(
        candidates=dict(candidates),
        known_mondo_ids=set(graph.nodes),
    )


def approve_mapping(
    resolver: IdentityResolver,
    external_id: str,
    mondo_id: str,
) -> None:
    """Compatibility with the earlier approve_mapping function."""
    resolver.approve_mapping(external_id, mondo_id)
