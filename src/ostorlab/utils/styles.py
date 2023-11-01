"""Define methods to style components for console."""

STYLE_RISK_MAP = {
    "CRITICAL": "[bold bright_white on #263238]Critical[/]",
    "HIGH": "[bold bright_white on #F55246]High[/]",
    "MEDIUM": "[bold bright_white on #FF9800]Medium[/]",
    "LOW": "[bold bright_white on #FDDB45]Low[/]",
    "POTENTIALLY": "[bold bright_white on #A6A6A6]Potentially[/]",
    "HARDENING": "[bold bright_white on #A438B6]Hardening[/]",
    "SECURE": "[bold bright_white on green #2D6B32]Secure[/]",
    "INFO": "[bold bright_white on #036CDB]Info[/]",
    "IMPORTANT": "[bold bright_white on #43A047]Important[/]",
}


def style_risk(risk: str) -> str:
    """Stylize the risk with colors."""
    return STYLE_RISK_MAP.get(risk, risk)


def style_progress(progress: str) -> str:
    """Stylize the scan progress with colors."""
    if progress == "done":
        return "[bold green4]Done[/]"
    if progress == "error":
        return "[bold magenta]Error[/]"
    if progress == "not_started":
        return "[bold bright_black]Not Started[/]"
    if progress == "stopped":
        return "[bold bright_red]Stopped[/]"
    if progress == "in_progress":
        return "[bold bright_cyan]Running[/]"
    else:
        return progress


def style_asset(asset: str) -> str:
    """Stylize the scan asset with colors and emojis."""
    if asset == "android_store":
        return "[bold green4]:iphone: Android Store[/]"
    elif asset == "ios_store":
        return "[bold bright_white]:apple: iOS Store[/]"
    elif asset == "android":
        return "[bold bright_green]:iphone: Android[/]"
    elif asset == "ios":
        return "[bold white]:apple: iOS[/]"
    else:
        return asset
