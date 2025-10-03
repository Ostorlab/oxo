from ostorlab.runtimes.proto import agent_instance_settings_pb2


def testAgentInstanceSettings_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    settings = agent_instance_settings_pb2.AgentInstanceSettings()
    settings.key = "test-key"
    settings.bus_url = "amqp://localhost:5672"
    settings.bus_exchange_topic = "test_exchange"
    settings.bus_management_url = "http://localhost:15672"
    settings.bus_vhost = "/"
    settings.replicas = 1
    settings.mem_limit = 512000000
    settings.restart_policy = "unless-stopped"

    arg = settings.args.add()
    arg.name = "test_arg"
    arg.type = "string"
    arg.value = b"test_value"

    port_mapping = settings.open_ports.add()
    port_mapping.source_port = 8080
    port_mapping.destination_port = 8080

    settings.constraints.append("cpu=1")
    settings.mounts.append("/tmp:/tmp")

    serialized = settings.SerializeToString()
    deserialized_settings = agent_instance_settings_pb2.AgentInstanceSettings()
    deserialized_settings.ParseFromString(serialized)

    assert deserialized_settings.key == "test-key"
    assert deserialized_settings.bus_url == "amqp://localhost:5672"
    assert deserialized_settings.bus_exchange_topic == "test_exchange"
    assert deserialized_settings.replicas == 1
    assert deserialized_settings.mem_limit == 512000000
    assert len(deserialized_settings.args) == 1
    assert deserialized_settings.args[0].name == "test_arg"
    assert deserialized_settings.args[0].value == b"test_value"
    assert len(deserialized_settings.open_ports) == 1
    assert deserialized_settings.open_ports[0].source_port == 8080


def testAgentInstanceSettings_whenCreateEmpty_shouldHaveDefaultValues():
    settings = agent_instance_settings_pb2.AgentInstanceSettings()

    assert settings.key == ""
    assert settings.bus_url == ""
    assert settings.bus_exchange_topic == ""
    assert settings.replicas == 0
    assert settings.mem_limit == 0
    assert len(settings.args) == 0
    assert len(settings.open_ports) == 0
    assert len(settings.constraints) == 0


def testAgentInstanceSettings_whenSerializeEmpty_shouldDeserializeToEmpty():
    settings = agent_instance_settings_pb2.AgentInstanceSettings()

    serialized = settings.SerializeToString()
    deserialized_settings = agent_instance_settings_pb2.AgentInstanceSettings()
    deserialized_settings.ParseFromString(serialized)

    assert deserialized_settings.key == ""
    assert deserialized_settings.bus_url == ""
    assert deserialized_settings.bus_exchange_topic == ""
    assert deserialized_settings.replicas == 0
    assert deserialized_settings.mem_limit == 0
    assert len(deserialized_settings.args) == 0
    assert len(deserialized_settings.open_ports) == 0
    assert len(deserialized_settings.constraints) == 0
