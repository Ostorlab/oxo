"""Module responsible for installing an agent : Pulling the image from the ostorlab registry."""
import click
import docker

from ostorlab.cli import console as cli_console
from ostorlab.apis import public_runner
from ostorlab.apis import authenticated_runner
from ostorlab.apis import get_agent_details
from ostorlab import configuration_manager

console = cli_console.Console()


def _parse_repository_tag(repo_name):
    parts = repo_name.rsplit('@', 1)
    if len(parts) == 2:
        return tuple(parts)
    parts = repo_name.rsplit(':', 1)
    if len(parts) == 2 and '/' not in parts[1]:
        return tuple(parts)
    return repo_name, None

def get_repo_name_and_tag(repository, tag=None):
    repository, image_tag = _parse_repository_tag(repository)
    tag = tag or image_tag or 'latest'
    return repository, tag


def get_pull_logs(client, repository, tag=None, all_tags=False,  **kwargs):
    repository, tag = get_repo_name_and_tag(repository, tag)
    pull_log = client.api.pull(repository, tag=tag, stream=True, all_tags=all_tags, decode=True, **kwargs)
    for log in pull_log:
        yield log


def get_image(client, repository, tag=None, all_tags=False):
    repository, tag = get_repo_name_and_tag(repository, tag)
    name = f'{0}{2}{1}'.format(repository, tag, '@' if tag.startswith('sha256:') else ':')

    if not all_tags:
        return client.images.get(name)
    return client.list(repository)


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

    def is_image_present(agent_key):
        agent_key = agent_key.replace('/', '_').lower()
        docker_client = docker.from_env()
        try:
            docker_client.images.get(agent_key)
            return True
        except docker.errors.ImageNotFound:
            return False

    try:
        if is_image_present(agent_key):
            console.status(f'{agent_key} already exist.')

        else:
            with console.status('Pulling the image from the ostorlab store.'):
                docker_client = docker.from_env()
                pull_logs_generator = get_pull_logs(docker_client, agent_docker_location)
                console.progress(pull_logs_generator)
                agent_image = get_image(docker_client, agent_docker_location, tag)
                agent_key = agent_key.replace('/', '_').lower()
                agent_image.tag(repository=agent_key, tag=tag)

    except docker.errors.ImageNotFound as e:
        console.error(f'The provided agent key : {agent_key} does not seem to be public.')
        console.error('Make sure you are logged in and try again.')
        console.error('To log in use the following command : ostorlab auth login -u <username> -p <password>')
        raise click.exceptions.Exit(2) from e

    console.success(':white_check_mark: Installation successful.')
