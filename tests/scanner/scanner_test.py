"""Unit test for the scanner configuration module."""

from pytest_mock import plugin

from ostorlab.scanner import scanner_conf


def testScannerConfigFromJson_whenReceivingConfApiResponse_shouldCreateConfInstance() -> (
    None
):
    """Ensure the correct creation of the scanner configuration instance with the correct attributes."""
    api_response_data = {
        "data": {
            "scanners": {
                "scanners": [
                    {
                        "id": "42",
                        "name": "scanner_42",
                        "description": "scanner 42 description",
                        "config": {
                            "apiKey": "test-api-key",
                            "scanResourceRequirements": {
                                "agentgroup/ostorlab/agent_group42": {
                                    "cpuCount": 8,
                                    "memory": 17179869184,
                                    "disk": 53687091200,
                                }
                            },
                        },
                    }
                ]
            }
        }
    }

    scanner_conf_instance = scanner_conf.ScannerConfig.from_json(
        config=api_response_data,
    )
    assert scanner_conf_instance.api_key == "test-api-key"
    requirements = scanner_conf_instance.scan_resource_requirements[
        "agentgroup/ostorlab/agent_group42"
    ]
    assert requirements.cpu_count == 8
    assert requirements.memory == 17179869184
    assert requirements.disk == 53687091200


def testScannerConfigFromJson_whenResourceRequirementsMalformed_shouldSkipEntry(
    mocker: plugin.MockerFixture,
) -> None:
    api_response_data = {
        "data": {
            "scanners": {
                "scanners": [
                    {
                        "config": {
                            "scanResourceRequirements": {
                                "agentgroup/ostorlab/missing_disk": {
                                    "cpuCount": 4,
                                    "memory": 17179869184,
                                },
                                "agentgroup/ostorlab/invalid_cpu": {
                                    "cpuCount": "four",
                                    "memory": 17179869184,
                                    "disk": 53687091200,
                                },
                            }
                        }
                    }
                ]
            }
        }
    }

    warning = mocker.patch.object(scanner_conf.logger, "warning")

    scanner_conf_instance = scanner_conf.ScannerConfig.from_json(api_response_data)

    assert scanner_conf_instance.scan_resource_requirements == {}
    assert warning.call_args_list == [
        mocker.call(
            "Skipping malformed scan resource requirements entry: %r",
            "agentgroup/ostorlab/missing_disk",
        ),
        mocker.call(
            "Skipping malformed scan resource requirements entry: %r",
            "agentgroup/ostorlab/invalid_cpu",
        ),
    ]


def testScannerConfigFromJson_whenResourceRequirementsJsonString_shouldParseEntry() -> (
    None
):
    api_response_data = {
        "data": {
            "scanners": {
                "scanners": [
                    {
                        "config": {
                            "scanResourceRequirements": (
                                '{"agentgroup/ostorlab/test": {'
                                '"cpuCount": 8, "memory": 16, "disk": 32}}'
                            )
                        }
                    }
                ]
            }
        }
    }

    scanner_conf_instance = scanner_conf.ScannerConfig.from_json(api_response_data)

    assert scanner_conf_instance.scan_resource_requirements == {
        "agentgroup/ostorlab/test": scanner_conf.ScanResourceRequirements(
            cpu_count=8,
            memory=16,
            disk=32,
        )
    }


def testScannerConfigFromJson_whenResourceRequirementsInvalidJson_shouldLogWarning(
    mocker: plugin.MockerFixture,
) -> None:
    api_response_data = {
        "data": {
            "scanners": {
                "scanners": [{"config": {"scanResourceRequirements": "invalid json"}}]
            }
        }
    }

    warning = mocker.patch.object(scanner_conf.logger, "warning")

    scanner_conf_instance = scanner_conf.ScannerConfig.from_json(api_response_data)

    assert scanner_conf_instance.scan_resource_requirements == {}
    warning.assert_called_once_with("Invalid JSON in scanResourceRequirements")


def testScannerConfigFromJson_whenResourceRequirementsAbsent_returnsEmptyDict() -> None:
    api_response_data = {
        "data": {"scanners": {"scanners": [{"config": {"apiKey": "test-api-key"}}]}}
    }

    scanner_conf_instance = scanner_conf.ScannerConfig.from_json(api_response_data)

    assert scanner_conf_instance.scan_resource_requirements == {}
