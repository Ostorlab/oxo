import click


@click.group()
def cli():
    pass

@cli.group()
def scan():
    pass


@scan.command()
def mobile():
    """Command on cli1"""


@scan.command()
def android_store():
    """Command on cli1"""


@scan.command()
def ios_store():
    """Command on cli1"""


@cli.group()
def extension():
    pass


@extension.command()
def fetch():
    """Command on cli2"""
