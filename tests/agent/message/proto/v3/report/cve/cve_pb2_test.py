from ostorlab.agent.message.proto.v3.report.cve import cve_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly() -> (
    None
):
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


def testMessage_whenCreateEmpty_shouldHaveDefaultValues() -> None:
    msg = cve_pb2.Message()

    assert msg.cve_id == ""
    assert msg.cwe == 0
    assert msg.description == ""
    assert msg.published_date == 0
    assert msg.modified_date == 0
    assert len(msg.targets) == 0
    assert len(msg.references) == 0


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty() -> None:
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


def testMessage_whenNewOptionalFieldsSet_shouldSerializeAndDeserializeCorrectly() -> (
    None
):
    msg = cve_pb2.Message()
    msg.vuln_status = "Modified"
    msg.kev.date_added = "2024-04-12"
    msg.kev.due_date = "2024-05-03"
    msg.kev.required_action = "Apply updates per vendor instructions."
    msg.kev.vulnerability_name = "Example Vendor Buffer Overflow"
    msg.ssvc.exploitation = "active"
    msg.ssvc.automatable = "yes"
    msg.ssvc.technical_impact = "total"

    affected = msg.affected.add()
    affected.vendor = "example_vendor"
    affected.product = "example_product"
    affected.default_status = "unknown"
    less_than_version = affected.versions.add()
    less_than_version.version = "1.0.0"
    less_than_version.less_than = "1.2.0"
    less_than_version.status = "affected"
    less_than_version.version_type = "semver"
    less_than_or_equal_version = affected.versions.add()
    less_than_or_equal_version.version = "2.0.0"
    less_than_or_equal_version.less_than_or_equal = "2.1.0"
    less_than_or_equal_version.status = "affected"
    less_than_or_equal_version.version_type = "semver"

    msg.cvss_scores.v2.source = "nvd@nist.gov"
    msg.cvss_scores.v31.source = "nvd@nist.gov"
    msg.cvss_scores.v30.source = "cna@example.com"
    msg.cvss_scores.v40.source = "cna@example.com"

    serialized = msg.SerializeToString()
    deserialized_msg = cve_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.vuln_status == "Modified"
    assert deserialized_msg.kev.date_added == "2024-04-12"
    assert deserialized_msg.kev.due_date == "2024-05-03"
    assert deserialized_msg.kev.required_action == (
        "Apply updates per vendor instructions."
    )
    assert deserialized_msg.kev.vulnerability_name == "Example Vendor Buffer Overflow"
    assert deserialized_msg.ssvc.exploitation == "active"
    assert deserialized_msg.ssvc.automatable == "yes"
    assert deserialized_msg.ssvc.technical_impact == "total"
    assert len(deserialized_msg.affected) == 1
    assert deserialized_msg.affected[0].vendor == "example_vendor"
    assert deserialized_msg.affected[0].product == "example_product"
    assert deserialized_msg.affected[0].default_status == "unknown"
    assert len(deserialized_msg.affected[0].versions) == 2
    assert deserialized_msg.affected[0].versions[0].version == "1.0.0"
    assert deserialized_msg.affected[0].versions[0].less_than == "1.2.0"
    assert deserialized_msg.affected[0].versions[0].status == "affected"
    assert deserialized_msg.affected[0].versions[0].version_type == "semver"
    assert deserialized_msg.affected[0].versions[1].version == "2.0.0"
    assert deserialized_msg.affected[0].versions[1].less_than_or_equal == "2.1.0"
    assert deserialized_msg.affected[0].versions[1].status == "affected"
    assert deserialized_msg.affected[0].versions[1].version_type == "semver"
    assert deserialized_msg.cvss_scores.v2.source == "nvd@nist.gov"
    assert deserialized_msg.cvss_scores.v31.source == "nvd@nist.gov"
    assert deserialized_msg.cvss_scores.v30.source == "cna@example.com"
    assert deserialized_msg.cvss_scores.v40.source == "cna@example.com"


def testMessage_whenCreateEmpty_shouldLeaveNewFieldsUnset() -> None:
    msg = cve_pb2.Message()

    assert msg.HasField("vuln_status") is False
    assert msg.HasField("kev") is False
    assert msg.HasField("ssvc") is False
    assert msg.vuln_status == ""
    assert len(msg.affected) == 0
    assert msg.cvss_scores.v2.HasField("source") is False
    assert msg.cvss_scores.v31.HasField("source") is False
    assert msg.cvss_scores.v30.HasField("source") is False
    assert msg.cvss_scores.v40.HasField("source") is False
    assert msg.SerializeToString() == b""


def testMessage_whenParsingBytesWithoutNewFields_shouldLeaveNewFieldsUnset() -> None:
    msg = cve_pb2.Message()
    msg.cve_id = "CVE-2023-1234"
    msg.cwe = 79
    msg.description = "Test vulnerability description"
    msg.cvss_scores.v31.version = "3.1"

    serialized = msg.SerializeToString()
    deserialized_msg = cve_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.cve_id == "CVE-2023-1234"
    assert deserialized_msg.cwe == 79
    assert deserialized_msg.description == "Test vulnerability description"
    assert deserialized_msg.cvss_scores.v31.version == "3.1"
    assert deserialized_msg.HasField("vuln_status") is False
    assert deserialized_msg.HasField("kev") is False
    assert deserialized_msg.HasField("ssvc") is False
    assert len(deserialized_msg.affected) == 0
    assert deserialized_msg.cvss_scores.v31.HasField("source") is False


def testMessage_whenParsingHandWrittenNewFieldBytes_shouldDecodeByFieldNumber() -> None:
    # Tags: field 9 string 0x4a, field 10 message 0x52, KEV field 1 string 0x0a.
    serialized = b"\x4a\x08Analyzed\x52\x0c\x0a\x0a2024-04-12"
    msg = cve_pb2.Message()

    msg.ParseFromString(serialized)

    assert msg.vuln_status == "Analyzed"
    assert msg.HasField("kev") is True
    assert msg.kev.date_added == "2024-04-12"
