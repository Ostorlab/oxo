from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenExceptionDomainsProvided_roundTrips() -> None:
    data = {
        "path": "Payload/App.app/Info.plist",
        "bundle_id": "com.example.app",
        "allows_arbitrary_loads": False,
        "allows_arbitrary_loads_in_web_content": True,
        "exception_domains": [
            {
                "domain": "example.com",
                "includes_subdomains": True,
                "allows_insecure_http_loads": True,
                "minimum_tls_version": "TLSv1.0",
            }
        ],
    }

    serialized = agent_message.Message.from_data(
        "v3.fingerprint.file.ios.app_transport_security", data
    )
    deserialized = agent_message.Message.from_raw(
        "v3.fingerprint.file.ios.app_transport_security", serialized.raw
    )

    assert deserialized.data == data
