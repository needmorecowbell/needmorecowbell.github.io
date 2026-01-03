#!/usr/bin/env python3
"""
Rich Console Output Module

Provides centralized colored output for the publishing CLI using the rich library.
Colors:
- Green: Success messages
- Yellow: Warnings
- Red: Errors
- Cyan: Info/highlights
- Blue: Headers and section titles
"""

import sys
from rich.console import Console
from rich.theme import Theme

# Define custom theme for consistent styling
PUBLISH_THEME = Theme({
    "success": "green",
    "warning": "yellow",
    "error": "bold red",
    "info": "cyan",
    "header": "bold blue",
    "dim": "dim",
    "highlight": "bold cyan",
    "path": "italic cyan",
    "count": "bold magenta",
})

# Global console instance with custom theme
# highlight=False prevents auto-highlighting of numbers/strings which can interfere with tests
# width=None allows the console to auto-detect width or use a reasonable fallback
# soft_wrap=True prevents hard line breaks within text
console = Console(theme=PUBLISH_THEME, highlight=False, soft_wrap=True)

# Error console for stderr
error_console = Console(stderr=True, theme=PUBLISH_THEME, highlight=False, soft_wrap=True)

# Global quiet flag - controlled by CLI
# When quiet mode is enabled, only errors are printed
# Must be defined before any functions that reference it
_quiet_mode = False


def print_success(message: str) -> None:
    """Print a success message in green."""
    if not _quiet_mode:
        console.print(f"[success]{message}[/success]")


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    if not _quiet_mode:
        console.print(f"[warning]{message}[/warning]")


def print_error(message: str) -> None:
    """Print an error message in red to stdout.

    While conventionally errors go to stderr, for this CLI we keep all user-facing
    output on stdout for consistent capture and display, with errors styled in red.

    Args:
        message: The error message to print
    """
    console.print(f"[error]{message}[/error]")


def print_info(message: str) -> None:
    """Print an info message in cyan."""
    if not _quiet_mode:
        console.print(f"[info]{message}[/info]")


def print_header(message: str) -> None:
    """Print a header message in bold blue."""
    if not _quiet_mode:
        console.print(f"[header]{message}[/header]")


def print_dim(message: str) -> None:
    """Print a dimmed message."""
    if not _quiet_mode:
        console.print(f"[dim]{message}[/dim]")


def print_path(message: str) -> None:
    """Print a path in italic cyan."""
    if not _quiet_mode:
        console.print(f"[path]{message}[/path]")


def format_success(text: str) -> str:
    """Format text as success (for inline use)."""
    return f"[success]{text}[/success]"


def format_warning(text: str) -> str:
    """Format text as warning (for inline use)."""
    return f"[warning]{text}[/warning]"


def format_error(text: str) -> str:
    """Format text as error (for inline use)."""
    return f"[error]{text}[/error]"


def format_info(text: str) -> str:
    """Format text as info (for inline use)."""
    return f"[info]{text}[/info]"


def format_highlight(text: str) -> str:
    """Format text as highlighted (for inline use)."""
    return f"[highlight]{text}[/highlight]"


def format_dim(text: str) -> str:
    """Format text as dimmed (for inline use)."""
    return f"[dim]{text}[/dim]"


def format_count(text: str) -> str:
    """Format a count/number (for inline use)."""
    return f"[count]{text}[/count]"


def print_validation_passed(message: str = "VALIDATION PASSED") -> None:
    """Print a validation passed message."""
    if not _quiet_mode:
        console.print(f"[success]{message}[/success]")


def print_validation_failed(message: str = "VALIDATION FAILED") -> None:
    """Print a validation failed message."""
    # Validation failures are errors, so always print
    console.print(f"[error]{message}[/error]")


def print_validation_warning(message: str) -> None:
    """Print a validation warning message."""
    if not _quiet_mode:
        console.print(f"[warning]{message}[/warning]")


def print_section_header(title: str, width: int = 60) -> None:
    """Print a section header with separator lines."""
    if not _quiet_mode:
        console.print()
        console.print("[header]" + "=" * width + "[/header]")
        console.print(f"[header]{title}[/header]")
        console.print("[header]" + "=" * width + "[/header]")


def print_subsection(title: str, width: int = 60) -> None:
    """Print a subsection header with separator line."""
    if not _quiet_mode:
        console.print("-" * width)
        console.print(f"[header]{title}[/header]")
        console.print("-" * width)


def print_separator(width: int = 60) -> None:
    """Print a separator line."""
    if not _quiet_mode:
        console.print("=" * width)


def print_ok() -> None:
    """Print 'OK' in green for validation output."""
    if not _quiet_mode:
        console.print("  [success]OK[/success]")


def print_skip(message: str) -> None:
    """Print a skip message (dimmed)."""
    if not _quiet_mode:
        console.print(f"  [dim][SKIP][/dim] {message}")


def print_status_line(label: str, value: str, label_width: int = 14) -> None:
    """Print a status line with label and value.

    Args:
        label: The label (left side)
        value: The value (right side)
        label_width: Width to pad the label to
    """
    if not _quiet_mode:
        console.print(f"{label:<{label_width}} {value}")


def print_publish_complete() -> None:
    """Print a publish complete banner."""
    if not _quiet_mode:
        console.print()
        console.print("[success]" + "=" * 60 + "[/success]")
        console.print("[success]PUBLISH COMPLETE[/success]")
        console.print("[success]" + "=" * 60 + "[/success]")


def print_dry_run_banner() -> None:
    """Print a dry run notice."""
    if not _quiet_mode:
        console.print("[warning][DRY RUN][/warning] No changes will be made.")


# ============================================================
# Quiet Mode Support
# ============================================================


def set_quiet(enabled: bool) -> None:
    """Set the global quiet mode.

    When quiet mode is enabled, only error messages are printed.
    All other output (success, info, warnings, headers, etc.) is suppressed.

    Args:
        enabled: Whether quiet mode is enabled
    """
    global _quiet_mode
    _quiet_mode = enabled


def is_quiet() -> bool:
    """Check if quiet mode is enabled.

    Returns:
        True if quiet mode is enabled
    """
    return _quiet_mode


# ============================================================
# Verbose Logging Support
# ============================================================

# Global verbose flag - controlled by CLI
_verbose_mode = False


def set_verbose(enabled: bool) -> None:
    """Set the global verbose mode.

    Args:
        enabled: Whether verbose logging is enabled
    """
    global _verbose_mode
    _verbose_mode = enabled


def is_verbose() -> bool:
    """Check if verbose mode is enabled.

    Returns:
        True if verbose mode is enabled
    """
    return _verbose_mode


def print_verbose(message: str) -> None:
    """Print a verbose log message (only if verbose mode is enabled and not quiet).

    Args:
        message: The message to print
    """
    if _verbose_mode and not _quiet_mode:
        console.print(f"[dim]  → {message}[/dim]")


def print_verbose_step(step: str, description: str) -> None:
    """Print a verbose step indicator with description.

    Args:
        step: Short step identifier (e.g., "PARSE", "TRANSFORM")
        description: What this step is doing
    """
    if _verbose_mode and not _quiet_mode:
        console.print(f"[dim]  [{step:12}][/dim] {description}")


def print_verbose_detail(key: str, value: str) -> None:
    """Print a verbose detail line (key: value format).

    Args:
        key: The label
        value: The value
    """
    if _verbose_mode and not _quiet_mode:
        console.print(f"[dim]    {key}: {value}[/dim]")


def print_verbose_list(items: list, prefix: str = "•") -> None:
    """Print a list of items in verbose mode.

    Args:
        items: List of items to print
        prefix: Prefix character for each item
    """
    if _verbose_mode and not _quiet_mode:
        for item in items:
            console.print(f"[dim]    {prefix} {item}[/dim]")
