from ostorlab.agent.message.proto.v3.report.ticket import (
    ticket_pb2,
)


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    msg = ticket_pb2.Message()
    msg.ticket_id = "TICKET-123"
    msg.title = "New Vulnerability Found"
    msg.description = "A new critical vulnerability was detected."

    comment1 = msg.comments.add()
    comment1.author = "author-1"
    comment1.message = "you need to do X and Y"

    comment2 = msg.comments.add()
    comment2.author = "author-2"
    comment2.message = "you need to do Z"

    serialized = msg.SerializeToString()
    deserialized_msg = ticket_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.ticket_id == "TICKET-123"
    assert deserialized_msg.title == "New Vulnerability Found"
    assert deserialized_msg.description == "A new critical vulnerability was detected."
    assert len(deserialized_msg.comments) == 2
    assert deserialized_msg.comments[0].author == "author-1"
    assert deserialized_msg.comments[0].message == "you need to do X and Y"
    assert deserialized_msg.comments[1].author == "author-2"
    assert deserialized_msg.comments[1].message == "you need to do Z"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    msg = ticket_pb2.Message()

    assert msg.ticket_id == ""
    assert msg.title == ""
    assert msg.description == ""
    assert len(msg.comments) == 0


def testComment_whenCreateWithDefaults_shouldHaveCorrectDefaults():
    comment = ticket_pb2.Comments()
    comment.author = "test_author"

    assert comment.author == "test_author"
    assert comment.message == ""


def testMessage_whenTicketKeySet_shouldSerializeAndDeserializeCorrectly():
    msg = ticket_pb2.Message()
    msg.title = "Test Ticket"
    msg.description = "Test description."
    msg.ticket_key = "PROJ-123"

    serialized = msg.SerializeToString()
    deserialized_msg = ticket_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.ticket_key == "PROJ-123"


def testMessage_whenTicketKeyNotSet_shouldDefaultToEmpty():
    msg = ticket_pb2.Message()

    assert msg.ticket_key == ""
