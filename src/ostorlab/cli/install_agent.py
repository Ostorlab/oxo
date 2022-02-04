"""Module responsible for installing an agent : Pulling the image from the ostorlab registry."""
import click
import docker

from ostorlab.cli import console as cli_console
from ostorlab.apis import public_runner
from ostorlab.apis import authenticated_runner
from ostorlab.apis import get_agent_details
from ostorlab import configuration_manager

console = cli_console.Console()


def install(agent_key: str, tag: str = '') -> None:
    """Install an agent : Fetch the docker file location of the agent corresponding to the agent_key,
    and pull the image from the registry.

    Args:
        agent_key: key of the agent in agent/org/agentName format.
        tag: tag of the docker image.

    Returns:
        None
    """
    config_manager = configuration_manager.ConfigurationManager()

    if config_manager.get_api_key_id():
        runner = authenticated_runner.AuthenticatedAPIRunner()
    else:
        runner = public_runner.PublicAPIRunner()

    response = runner.execute(get_agent_details.AgentAPIRequest(agent_key))

    if 'errors' in response:
        console.error(f'The provided agent key : {agent_key} does not correspond to any agent.')
        console.error('Please make sure you have the correct agent key.')
        raise click.exceptions.Exit(2)
    else:
        agent_details = response['data']['agent']
        agent_docker_location = agent_details['dockerLocation']

    try:
        with console.status('Pulling the image from the registery.'):
            docker_client = docker.from_env()
            agent_image = docker_client.images.pull(agent_docker_location)
            agent_key = agent_key.replace('/', '_').lower()
            agent_image.tag(repository=agent_key, tag=tag)

    except docker.errors.ImageNotFound as e:
        console.error(f'The provided agent key : {agent_key} does not seem to be public.')
        console.error('Make sure you are logged in and try again.')
        console.error('To log in use the following command : ostorlab auth login -u <username> -p <password>')
        raise click.exceptions.Exit(2) from e

    console.success(':white_check_mark: Installation successful.')
