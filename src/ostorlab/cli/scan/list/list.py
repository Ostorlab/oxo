"""Module for the command list inside the group scan.
This module takes care of listing all the remote or local scans.
Example of usage:
    - ostorlab scan list --source=source."""

import click

from ostorlab.cli import console as cli_console
from ostorlab.cli.scan import scan
from ostorlab.runtimes.local.models import models
from ostorlab.utils import styles

console = cli_console.Console()


@scan.command(name="list")
@click.option(
    "--page", "-p", help="Page number of scans you would like to see.", default=1
)
@click.option("--elements", "-e", help="Number of scans to show per page.", default=10)
@click.pass_context
def list_scans(ctx: click.core.Context, page: int, elements: int) -> None:
    """List all your scans.\n
    Usage:\n
        - ostorlab scan --runtime=runtime list
    """
    runtime_instance = ctx.obj["runtime"]
    with console.status("Fetching scans"):
        scans = runtime_instance.list(page=page, number_elements=elements)
        if scans is not None:
            console.success("Scans listed successfully.")
            columns = {
                "Id": "id",
                "Asset": "asset",
                "Created Time": "created_time",
                "Progress": "progress",
            }
            title = f"Showing {len(scans)} Scans"

            data = [
                {
                    "id": str(s.id),
                    "asset": s.asset or _prepare_asset_str(s.id),
                    "created_time": str(s.created_time),
                    "progress": styles.style_progress(s.progress),
                }
                for s in scans
            ]

            console.table(columns=columns, data=data, title=title)
        else:
            console.error("Error fetching scan list.")


def _prepare_asset_str(scan_id: int) -> str:
    """Prepare the asset string for the scan."""
    with models.Database() as session:
        assets = (
            session.query(models.Asset).filter(models.Asset.scan_id == scan_id).all()
        )
        if len(assets) == 0:
            return "N/A"

        asset_list = []
        for asset in assets:
            asset_type = asset.type
            if asset_type == "android_file":
                android_file_asset = (
                    session.query(models.AndroidFile).filter_by(id=asset.id).first()
                )
                asset_list.append(f"Android File: {android_file_asset.path}")
            elif asset_type == "ios_file":
                ios_file_asset = (
                    session.query(models.IosFile).filter_by(id=asset.id).first()
                )
                asset_list.append(f"IOS File: {ios_file_asset.path}")
            elif asset_type == "android_store":
                android_store_asset = (
                    session.query(models.AndroidStore).filter_by(id=asset.id).first()
                )
                asset_list.append(
                    f"Android Store: {android_store_asset.application_name or android_store_asset.package_name}"
                )
            elif asset_type == "ios_store":
                ios_store_asset = (
                    session.query(models.IosStore).filter_by(id=asset.id).first()
                )
                asset_list.append(
                    f"IOS Store: {ios_store_asset.application_name or ios_store_asset.bundle_id}"
                )
            elif asset_type == "network":
                ips = (
                    session.query(models.IPRange)
                    .filter_by(network_asset_id=asset.id)
                    .all()
                )
                networks_str = ", ".join(f"{ip.host}/{ip.mask or 32}" for ip in ips)
                asset_list.append(f"Network(s): {networks_str}")
            elif asset_type == "urls":
                urls = (
                    session.query(models.Link).filter_by(urls_asset_id=asset.id).all()
                )
                urls_str = ", ".join(url.url for url in urls)
                asset_list.append(f"Url(s): {urls_str}")
            elif asset_type == "domain_asset":
                domain = (
                    session.query(models.DomainName)
                    .filter_by(domain_asset_id=asset.id)
                    .first()
                )
                asset_list.append(f"Domain: {domain.name}")
            else:
                raise NotImplementedError(f"Asset type {asset.type} not implemented.")

        return ", ".join(asset_list)
