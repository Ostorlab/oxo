"""Scan module that handles running a scan using a list of agent keys and a target asset."""

from typing import Optional

import click

from ostorlab.cli.rootcli import rootcli
from ostorlab.runtimes import registry
from ostorlab.cli import input_validators


@rootcli.group()
@click.option(
    "--runtime",
    type=click.Choice(["local", "litelocal", "cloud", "hybrid"]),
    help="""Runtime is in charge of preparing the environment to trigger a scan.\n
                    Specify which runtime to use: \n
                    local: on you local machine\n
                    litelocal: stripped down local runtime\n
                    cloud: on Ostorlab cloud, (requires login)\n
                    hybrid: running partially on Ostorlab cloud and partially on the local machine\n
                   """,
    default="local",
    required=True,
)
@click.option(
    "--bus-url",
    help="Bus URL, this flag is restricted to the lite local runtime.",
    required=False,
    hidden=True,
)
@click.option(
    "--bus-vhost",
    help="Bus vhost, this flag is restricted to the lite local runtime.",
    required=False,
    hidden=True,
)
@click.option(
    "--bus-management-url",
    help="Bus management URL, this flag is restricted to the lite local runtime.",
    required=False,
    hidden=True,
)
@click.option(
    "--bus-exchange-topic",
    help="Bus exchange topic, this flag is restricted to the lite local runtime.",
    required=False,
    hidden=True,
)
@click.option(
    "--network",
    help="Docker network to attach service and agents to.",
    required=False,
    hidden=True,
)
@click.option(
    "--redis-url",
    help="Redis URL, this flag is restricted to the lite local runtime.",
    required=False,
    hidden=True,
)
@click.option(
    "--scan-id",
    help="Scan id, this flag is restricted to the lite local runtime..",
    required=False,
    hidden=True,
)
@click.option("--tracing/--no-tracing", help="Enable tracing mode", default=False)
@click.option(
    "--tracing-collector-url",
    help="Tracing Collector URL, this flag is restricted to the lite local runtime.",
    required=False,
    hidden=True,
)
@click.option(
    "--mq-exposed-ports",
    help="Ports to expose on RabbitMQ service_port1:host_port1,service_port2:host_port2",
    required=False,
    hidden=True,
    callback=input_validators.validate_port_binding_input,
)
@click.pass_context
def scan(
    ctx: click.core.Context,
    runtime: str,
    bus_url: Optional[str] = None,
    bus_vhost: Optional[str] = None,
    bus_management_url: Optional[str] = None,
    bus_exchange_topic: Optional[str] = None,
    scan_id: Optional[str] = None,
    network: Optional[str] = None,
    redis_url: Optional[str] = None,
    tracing: bool = False,
    tracing_collector_url: Optional[str] = None,
    mq_exposed_ports: Optional[str] = None,
) -> None:
    """Use scan [subcommand] to list, start or stop a scan.\n
    Examples:\n
        - To show list of scans:\n
        ostorlab scan list\n
        - To stop a scan:\n
        ostorlab scan stop <scan-id>\n
    """
    try:
        if mq_exposed_ports is not None:
            exposed_ports_list = mq_exposed_ports.split(",")
            mq_exposed_ports = {
                int(port.split(":")[0]): int(port.split(":")[1])
                for port in exposed_ports_list
            }
        runtime_instance = registry.select_runtime(
            runtime,
            scan_id=scan_id,
            bus_url=bus_url,
            bus_vhost=bus_vhost,
            bus_management_url=bus_management_url,
            bus_exchange_topic=bus_exchange_topic,
            network=network,
            redis_url=redis_url,
            tracing=tracing,
            tracing_collector_url=tracing_collector_url,
            mq_exposed_ports=mq_exposed_ports,
            gcp_logging_credential=ctx.obj.get("gcp_logging_credential"),
        )
        ctx.obj["runtime"] = runtime_instance
    except registry.RuntimeNotFoundError as e:
        raise click.ClickException(
            f"The selected runtime {runtime} is not supported."
        ) from e
    except ValueError as e:
        raise click.ClickException(f"Error initializing runtime {runtime}.") from e
