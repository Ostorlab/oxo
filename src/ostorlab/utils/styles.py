"""Define methods to style components for console."""

from rich import emoji, text

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
    "UNKNOWN": "[bold bright_white on #AAAA90]Unknown[/]",
}


def _to_text(styled: str | None, fallback: str | None) -> text.Text:
    """Renders a styled markup template, falling back to the unstyled value.

    The styles are returned as `Text` instead of markup strings, so that the console renders them
    without parsing the surrounding untrusted values, like asset URLs, as markup.

    Args:
        styled: The markup template of the styled value, None if the value has no style.
        fallback: The raw value to show unstyled, None for scans with no progress or rating.

    Returns:
        The renderable styled value, empty if there is no value to show.
    """
    if styled is None:
        return text.Text(fallback if fallback is not None else "")
    return text.Text.from_markup(emoji.Emoji.replace(styled))


def style_risk(risk: str | None) -> text.Text:
    """Stylize the risk with colors."""
    if risk is None:
        return _to_text(None, risk)
    return _to_text(STYLE_RISK_MAP.get(risk), risk)


def style_progress(progress: str | None) -> text.Text:
    """Stylize the scan progress with colors."""
    if progress == "done":
        return _to_text("[bold green4]Done[/]", progress)
    if progress == "error":
        return _to_text("[bold magenta]Error[/]", progress)
    if progress == "not_started":
        return _to_text("[bold bright_black]Not Started[/]", progress)
    if progress == "stopped":
        return _to_text("[bold bright_red]Stopped[/]", progress)
    if progress == "in_progress":
        return _to_text("[bold bright_cyan]Running[/]", progress)
    else:
        return _to_text(None, progress)


def style_asset(asset: str | None) -> text.Text:
    """Stylize the scan asset with colors and emojis."""
    if asset == "android_store":
        return _to_text("[bold green4]:iphone: Android Store[/]", asset)
    elif asset == "ios_store":
        return _to_text("[bold bright_white]:apple: iOS Store[/]", asset)
    elif asset == "android":
        return _to_text("[bold bright_green]:iphone: Android[/]", asset)
    elif asset == "ios":
        return _to_text("[bold white]:apple: iOS[/]", asset)
    else:
        return _to_text(None, asset)
