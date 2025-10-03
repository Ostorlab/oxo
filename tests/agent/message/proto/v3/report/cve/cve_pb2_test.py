import pytest

from ostorlab.agent.message.proto.v3.report.cve import cve_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    msg = cve_pb2.Message()
    msg.cve_id = "CVE-2023-1234"
    msg.cwe = 79
    msg.description = "Test vulnerability description"
    msg.published_date = 1640995200
    msg.modified_date = 1640995200
    
    target = msg.targets.add()
    cpe_match = target.cpe_matches.add()
    cpe_match.part = "a"
    cpe_match.vendor = "test_vendor"
    cpe_match.product = "test_product"
    cpe_match.vulnerable = True
    
    reference = msg.references.add()
    reference.url = "https://example.com/vuln"
    reference.source = "NVD"
    reference.tags.append("Patch")
    
    serialized = msg.SerializeToString()
    deserialized_msg = cve_pb2.Message()
    deserialized_msg.ParseFromString(serialized)
    
    assert deserialized_msg.cve_id == "CVE-2023-1234"
    assert deserialized_msg.cwe == 79
    assert deserialized_msg.description == "Test vulnerability description"
    assert deserialized_msg.published_date == 1640995200
    assert deserialized_msg.modified_date == 1640995200
    assert len(deserialized_msg.targets) == 1
    assert len(deserialized_msg.targets[0].cpe_matches) == 1
    assert deserialized_msg.targets[0].cpe_matches[0].vendor == "test_vendor"
    assert len(deserialized_msg.references) == 1
    assert deserialized_msg.references[0].url == "https://example.com/vuln"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    msg = cve_pb2.Message()
    
    assert msg.cve_id == ""
    assert msg.cwe == 0
    assert msg.description == ""
    assert msg.published_date == 0
    assert msg.modified_date == 0
    assert len(msg.targets) == 0
    assert len(msg.references) == 0


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    msg = cve_pb2.Message()
    
    serialized = msg.SerializeToString()
    deserialized_msg = cve_pb2.Message()
    deserialized_msg.ParseFromString(serialized)
    
    assert deserialized_msg.cve_id == ""
    assert deserialized_msg.cwe == 0
    assert deserialized_msg.description == ""
    assert deserialized_msg.published_date == 0
    assert deserialized_msg.modified_date == 0
    assert len(deserialized_msg.targets) == 0
    assert len(deserialized_msg.references) == 0