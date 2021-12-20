import logging

import click

from ostorlab.apis import runner as apis_runner
from ostorlab.apis import scan as apis_scan
from ostorlab.cli.rootcli import scan

logger = logging.getLogger(__name__)


@scan.command()
def android_store():
    """Command on cli1"""


@scan.command()
@click.option('--plan', type=click.Choice(['free']), help='Plan.', required=True)
@click.option('--platform', type=click.Choice(['android', 'ios']), help='platform.', required=True)
@click.option('--application', type=click.Path(readable=True, exists=True), help='application.', required=True)
@click.option('--title', '-t', help='Scan title.')
@click.option('--username', '-u', help='Ostorlab platform username.')
@click.option('--password', '-p', help='Ostorlab platform password.')
@click.option('--proxy', '-X', help='Proxy to route HTTPS requests through.')
@click.option('--tlsverify/--no-tlsverify', default=True)
@click.pass_context
def mobile(ctx, plan, platform, application):
    try:
        api_runner = apis_runner.Runner(username=ctx.obj['username'], password=ctx.obj['password'],
                                        proxy=ctx.obj['proxy'], verify=ctx.obj['tlsverify'])
        api_runner.authenticate()

        with open(application, 'rb') as o_app:
            logger.debug('application %s', application)
            create_request = apis_scan.CreateMobileScanAPIRequest(
                title=ctx.obj['title'],
                asset_type=apis_scan.MobileAssetType[platform.upper()],
                plan=apis_scan.Plan[plan.upper()],
                application=o_app)
            response = api_runner.execute(create_request)
            logger.debug(response)

    except apis_runner.AuthenticationError:
        logger.error('Authentication error, please check that your credentials are valid.')


@scan.command()
def ios_store():
    """Command on cli1"""
