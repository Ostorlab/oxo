"""Common logic for Mobile Assets of type .APK package file AAB package file and IPA .
This module takes care of preparing the application file and calling the create mobile scan API.
"""
import io
import click

from ostorlab.cli.ci_scan.run import run
from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis.runners import runner as base_runner
from ostorlab.apis import scan_create as scan_create_api


def run_mobile_scan(ctx: click.core.Context, file: io.FileIO, asset_type: scan_create_api.MobileAssetType) -> None:
    """Create scan for mobile application package file."""
    ci_logger = ctx.obj['ci_logger']
    if ctx.obj.get('api_key'):
        scan_profile = ctx.obj['scan_profile']
        title = ctx.obj['title']
        break_on_risk_rating = ctx.obj['break_on_risk_rating']
        max_wait_minutes = ctx.obj['max_wait_minutes']
        runner = authenticated_runner.AuthenticatedAPIRunner(api_key=ctx.obj.get('api_key'))
        try:
            scan_result = runner.execute(
                scan_create_api.CreateMobileScanAPIRequest(title=title,
                                                           asset_type=asset_type,
                                                           scan_profile=scan_profile,
                                                           application=file))
            scan_id = scan_result.get('data').get('createMobileScan').get('scan').get('id')
            ci_logger.output(name='scan_id', value=scan_id)
            ci_logger.info(f'Scan created with id {scan_id}.')
            if break_on_risk_rating is not None:
                run.apply_break_scan_risk_rating(break_on_risk_rating, scan_id, max_wait_minutes, runner, ci_logger)

        except base_runner.ResponseError as e:
            ci_logger.error(f'Could not start the scan. {e}')
            raise click.exceptions.Exit(2) from e
        except TimeoutError:
            ci_logger.error('The scan is still running.')
            raise click.exceptions.Exit(2) from None
    else:
        ci_logger.error('API key not not provided.')
        raise click.exceptions.Exit(2) from None
