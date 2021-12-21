import click


@click.group()
def rootcli():
    pass


@rootcli.group()
def scan():
    pass


@rootcli.group()
def agent():
    pass


@rootcli.group()
def agentgroup():
    pass


@rootcli.group()
def auth():
    pass
