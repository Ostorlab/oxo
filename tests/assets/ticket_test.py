"""Unit tests for Ticket asset."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.report.ticket import ticket_pb2
from ostorlab.assets import ticket


def testTicketToProto_whenValidData_generatesProto() -> None:
    asset = ticket.Ticket(
        title="Sample Ticket",
        ticket_id="TCK-123",
        ticket_key="PROJ-123",
        description="A sample ticket description",
        comments=[
            ticket.Comment(author="alice", message="high priority"),
            ticket.Comment(author="bob", message="bug confirmed"),
        ],
    )
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.report.ticket", raw)
    assert isinstance(unraw, ticket_pb2.Message)
    assert unraw.title == "Sample Ticket"
    assert unraw.ticket_id == "TCK-123"
    assert unraw.ticket_key == "PROJ-123"
    assert unraw.description == "A sample ticket description"
    assert unraw.comments[0].author == "alice"
    assert unraw.comments[0].message == "high priority"
    assert unraw.comments[1].author == "bob"
    assert unraw.comments[1].message == "bug confirmed"
