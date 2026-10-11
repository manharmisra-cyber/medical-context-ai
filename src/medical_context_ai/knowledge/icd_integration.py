
from dataclasses import dataclass
from typing import Any

from .icd_client import ICDClient
from .identity import IdentityResolver


@dataclass
class ICDRecord:
    entity_id: str
    title: str
    mondo_id: str | None
    raw: dict[str, Any]


class ICDIntegration:
    def __init__(
        self,
        resolver: IdentityResolver,
        client: ICDClient | None = None,
    ):
        self.resolver = resolver
        self.client = client or ICDClient()

    def fetch_entity(self, entity_number: str) -> ICDRecord:
        entity = self.client.get_entity(entity_number)

        entity_id = entity.get(
            "@id",
            f"http://id.who.int/icd/entity/{entity_number}",
        )

        title_data = entity.get("title", {})

        if isinstance(title_data, dict):
            title = title_data.get("@value", "Unknown")
        else:
            title = str(title_data)

        return ICDRecord(
            entity_id=entity_id,
            title=title,
            mondo_id=self.resolver.resolve(entity_id),
            raw=entity,
        )
