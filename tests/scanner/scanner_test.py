"""Unit test for the scanner configuration module."""
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
                            "harborAccountName": "robot_account",
                            "harborCredentials": "<secret_key>",
                            "busUrl": "nats://localhost:4222",
                            "busClusterId": "cluster_id",
                            "busClientName": "client_name",
                            "subjectBusConfigs": {
                                "subjectBusConfigs": [
                                    {"subject": "subject1", "queue": "queue1"}
                                ]
                            },
                        },
                    }
                ]
            }
        }
    }

    scanner_conf_instance = scanner_conf.ScannerConfig.from_json(
        config=api_response_data
    )
    assert scanner_conf_instance.bus_url == "nats://localhost:4222"
    assert scanner_conf_instance.bus_cluster_id == "cluster_id"
    assert scanner_conf_instance.bus_client_name == "client_name"
    assert scanner_conf_instance.registry_conf.username == "robot_account"
    assert scanner_conf_instance.registry_conf.token == "<secret_key>"
    assert scanner_conf_instance.subject_bus_configs[0].subject == "subject1"
    assert scanner_conf_instance.subject_bus_configs[0].queue == "queue1"
