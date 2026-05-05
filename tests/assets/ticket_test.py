"""Unit tests for Ticket asset."""

from ostorlab.agent.message import serializer
from ostorlab.assets import ticket


def testTicketToProto_whenValidData_generatesProto():
    asset = ticket.Ticket(
        title="Sample Ticket",
        ticket_id="TCK-123",
        description="A sample ticket description",
        comments=[
            ticket.Comment(author="alice", message="high priority"),
            ticket.Comment(author="bob", message="bug confirmed"),
        ],
    )
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.report.ticket", raw)
    assert unraw.title == "Sample Ticket"
    assert unraw.ticket_id == "TCK-123"
    assert unraw.description == "A sample ticket description"
    assert unraw.comments[0].author == "alice"
    assert unraw.comments[0].message == "high priority"
    assert unraw.comments[1].author == "bob"
    assert unraw.comments[1].message == "bug confirmed"
