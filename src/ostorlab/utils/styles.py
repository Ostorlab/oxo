"""Define methods to style components for console."""


def style_risk(risk: str) -> str:
    """Stylize the risk with colors."""
    if risk == 'HIGH':
        return '[bold bright_white on red]High[/]'
    elif risk == 'MEDIUM':
        return '[bold bright_white on yellow]Medium[/]'
    elif risk == 'LOW':
        return '[bold bright_white on bright_yellow]Low[/]'
    else:
        return risk


def style_progress(progress: str) -> str:
    """Stylize the scan progress with colors."""
    if progress == 'done':
        return '[bold green4]Done[/]'
    if progress == 'error':
        return '[bold magenta]Error[/]'
    if progress == 'not_started':
        return '[bold bright_black]Not Started[/]'
    if progress == 'stopped':
        return '[bold bright_red]Stopped[/]'
    if progress == 'in_progress':
        return '[bold bright_cyan]Running[/]'
    else:
        return progress


def style_asset(asset: str) -> str:
    """Stylize the scan asset with colors and emojis."""
    if asset == 'android_store':
        return '[bold green4]:iphone: Android Store[/]'
    elif asset == 'ios_store':
        return '[bold bright_white]:apple: iOS Store[/]'
    elif asset == 'android':
        return '[bold bright_green]:iphone: Android[/]'
    elif asset == 'ios':
        return '[bold white]:apple: iOS[/]'
    else:
        return asset
