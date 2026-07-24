"""Report asset."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
class Comment:
    """Comment message."""

    author: str | None = None
    message: str | None = None


@dataclasses.dataclass
@asset.selector("v3.report.ticket")
class Ticket(asset.Asset):
    """Ticket asset."""

    title: str
    description: str
    ticket_id: str | None = None
    comments: list[Comment] = dataclasses.field(default_factory=list)
    ticket_key: str | None = None

    def __str__(self) -> str:
        return f"Ticket {self.title}"

    @property
    def proto_field(self) -> str:
        return "ticket"
