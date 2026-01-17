"""
CLI interface for WireViz Doc.

Provides the `wvdoc` command with subcommands for building documentation,
resolving images, and linting harness YAML files.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich import print as rprint
from rich.panel import Panel
from rich.tree import Tree

from wireviz_doc import __version__
from wireviz_doc.output import close_file_logging, logger, setup_file_logging

app = typer.Typer(
    name="wvdoc",
    help="Generate factory-ready wiring documentation from YAML.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Global state
_verbose = False
_quiet = False


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        rprint(f"[bold cyan]wvdoc[/bold cyan] version [green]{__version__}[/green]")
        raise typer.Exit()


def check_graphviz() -> bool:
    """Check if Graphviz (dot) is available on the system."""
    return shutil.which("dot") is not None


def echo_info(message: str) -> None:
    """Print info message (respects quiet mode)."""
    if not _quiet:
        rprint(f"[cyan]ℹ[/cyan]  {message}")


def echo_success(message: str) -> None:
    """Print success message."""
    if not _quiet:
        rprint(f"[green]✓[/green]  {message}")


def echo_warning(message: str) -> None:
    """Print warning message."""
    rprint(f"[yellow]⚠[/yellow]  {message}")


def echo_error(message: str) -> None:
    """Print error message."""
    rprint(f"[red]✗[/red]  {message}")


def echo_debug(message: str) -> None:
    """Print debug message (only in verbose mode)."""
    if _verbose:
        rprint(f"[dim]→  {message}[/dim]")


def echo_header(title: str) -> None:
    """Print section header."""
    if not _quiet:
        rprint()
        rprint(f"[bold magenta]━━━ {title} ━━━[/bold magenta]")
        rprint()


def echo_file_created(path: Path) -> None:
    """Print file created message."""
    if not _quiet:
        rprint(f"  [green]✓[/green] Created [blue underline]{path}[/blue underline]")


@app.callback()
def main(
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose", "-v",
            help="Enable verbose output with debug information.",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet", "-q",
            help="Suppress non-essential output.",
        ),
    ] = False,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version", "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
) -> None:
    """
    [bold cyan]WireViz Doc[/bold cyan] - Generate factory-ready wiring documentation from YAML.

    Use [green]wvdoc build[/green] to generate documentation, [green]wvdoc lint[/green] to validate
    files, and [green]wvdoc images[/green] to resolve part images.
    """
    global _verbose, _quiet
    _verbose = verbose
    _quiet = quiet

    if not check_graphviz() and not quiet:
        echo_warning(
            "Graphviz (dot) not found. Install with: "
            "[dim]brew install graphviz[/dim] (macOS) or "
            "[dim]apt install graphviz[/dim] (Linux)"
        )


@app.command()
def build(
    files: Annotated[
        list[Path],
        typer.Argument(
            help="Harness YAML file(s) or glob pattern to build.",
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir", "-o",
            help="Output directory for generated files.",
        ),
    ] = Path("build"),
    format: Annotated[
        str,
        typer.Option(
            "--format", "-f",
            help="Output format(s): svg, pdf, or all.",
        ),
    ] = "all",
    template: Annotated[
        Optional[Path],
        typer.Option(
            "--template", "-t",
            help="Custom SVG template for output.",
            exists=True,
            dir_okay=False,
        ),
    ] = None,
    log_file: Annotated[
        bool,
        typer.Option(
            "--log-file",
            help="Write detailed log to build/<harness-id>/build.log",
        ),
    ] = False,
    log_level: Annotated[
        str,
        typer.Option(
            "--log-level",
            help="Log level for file logging: DEBUG, INFO, WARNING, ERROR.",
        ),
    ] = "DEBUG",
    allow_missing_images: Annotated[
        bool,
        typer.Option(
            "--allow-missing-images",
            help="Continue build even if part images are missing.",
        ),
    ] = False,
    ci: Annotated[
        bool,
        typer.Option(
            "--ci",
            help="CI mode: strict validation, no scraping, deterministic output.",
        ),
    ] = False,
) -> None:
    """
    Build documentation from harness YAML file(s).

    Generates SVG/PDF diagrams with title blocks, BOM, and wiring tables.

    [bold]Examples:[/bold]

        wvdoc build harness.yml

        wvdoc build "harnesses/*.harness.yml" --output-dir dist

        wvdoc build harness.yml --format pdf --log-file
    """
    import glob as glob_module
    from datetime import datetime

    start_time = datetime.now()

    # Expand glob patterns
    expanded_files: list[Path] = []
    for file_pattern in files:
        pattern_str = str(file_pattern)
        if "*" in pattern_str or "?" in pattern_str:
            matches = glob_module.glob(pattern_str, recursive=True)
            expanded_files.extend(Path(m) for m in matches)
        else:
            expanded_files.append(file_pattern)

    if not expanded_files:
        echo_error("No matching files found.")
        raise typer.Exit(code=1)

    # Validate files exist
    missing = [f for f in expanded_files if not f.exists()]
    if missing:
        for f in missing:
            echo_error(f"File not found: {f}")
        raise typer.Exit(code=1)

    echo_header("WireViz Doc Build")
    echo_info(f"Building {len(expanded_files)} file(s)")
    echo_debug(f"Output directory: {output_dir}")
    echo_debug(f"Format: {format}")
    if template:
        echo_debug(f"Template: {template}")
    if ci:
        echo_info("CI mode enabled (strict validation, no scraping)")

    errors = 0
    warnings = 0

    for harness_file in expanded_files:
        rprint(f"\n[bold cyan]▸ Processing {harness_file.name}[/bold cyan]")

        # Determine harness ID (would come from YAML metadata)
        harness_id = harness_file.stem.replace(".harness", "")
        harness_output_dir = output_dir / harness_id
        harness_output_dir.mkdir(parents=True, exist_ok=True)

        # Set up file logging if requested
        if log_file:
            log_path = setup_file_logging(
                harness_output_dir / "build.log",
                level=log_level,
            )
            logger.info(f"Building harness: {harness_file}")
            logger.info(f"Output directory: {harness_output_dir}")
            echo_debug(f"Log file: {log_path}")

        # TODO: Implement actual build pipeline
        # 1. Parse extended YAML
        # 2. Validate schema
        # 3. Resolve images
        # 4. Generate WireViz YAML
        # 5. Run WireViz
        # 6. Generate wiring table
        # 7. Compose final SVG/PDF
        # 8. Generate BOM TSV

        echo_warning("Build pipeline not yet implemented")
        warnings += 1

        # Placeholder output
        echo_file_created(harness_output_dir / "diagram.svg")
        echo_file_created(harness_output_dir / "diagram.pdf")
        echo_file_created(harness_output_dir / "bom.tsv")
        echo_file_created(harness_output_dir / "wiring_table.tsv")

        if log_file:
            logger.info("Build complete")
            close_file_logging()

    elapsed = (datetime.now() - start_time).total_seconds()

    # Summary
    rprint()
    if errors > 0:
        rprint("[red bold]BUILD FAILED[/red bold]")
    elif warnings > 0:
        rprint("[yellow]BUILD COMPLETE (with warnings)[/yellow]")
    else:
        rprint("[green bold]BUILD COMPLETE[/green bold]")

    # Show output tree
    if not _quiet:
        rprint()
        tree = Tree(f"[blue]{output_dir}[/blue]")
        for harness_file in expanded_files:
            harness_id = harness_file.stem.replace(".harness", "")
            branch = tree.add(f"[blue]{harness_id}/[/blue]")
            branch.add("[dim]diagram.svg[/dim]")
            branch.add("[dim]diagram.pdf[/dim]")
            branch.add("[dim]bom.tsv[/dim]")
            branch.add("[dim]wiring_table.tsv[/dim]")
            if log_file:
                branch.add("[dim]build.log[/dim]")
        rprint(tree)

    rprint(f"\n[dim]Completed in {elapsed:.2f}s[/dim]")

    if errors > 0:
        raise typer.Exit(code=1)
    elif warnings > 0:
        raise typer.Exit(code=2)


@app.command()
def lint(
    files: Annotated[
        list[Path],
        typer.Argument(help="Harness YAML file(s) to validate."),
    ],
    strict: Annotated[
        bool,
        typer.Option("--strict", help="Treat warnings as errors."),
    ] = False,
) -> None:
    """
    Validate harness YAML files against the schema.

    Checks for:
    - Schema validation errors
    - Missing part numbers
    - Invalid wire colors
    - Missing images
    - Invalid connections

    [bold]Examples:[/bold]

        wvdoc lint harness.yml

        wvdoc lint harness.yml --strict
    """
    echo_header("WireViz Doc Lint")

    total_errors = 0
    total_warnings = 0

    for harness_file in files:
        if not harness_file.exists():
            echo_error(f"File not found: {harness_file}")
            total_errors += 1
            continue

        rprint(f"\n[bold cyan]▸ Validating {harness_file.name}[/bold cyan]")

        # TODO: Implement actual validation
        errors: list[str] = []
        warnings: list[str] = []
        warnings.append("Validation not yet implemented")

        for error in errors:
            echo_error(error)
        for warning in warnings:
            echo_warning(warning)

        if not errors and not warnings:
            echo_success("Valid")

        total_errors += len(errors)
        total_warnings += len(warnings)

    rprint()

    if total_errors > 0:
        echo_error(f"Validation failed: {total_errors} error(s), {total_warnings} warning(s)")
        raise typer.Exit(code=1)
    elif total_warnings > 0 and strict:
        echo_warning(f"Strict mode: {total_warnings} warning(s) treated as errors")
        raise typer.Exit(code=1)
    elif total_warnings > 0:
        echo_warning(f"Validation passed with {total_warnings} warning(s)")
        raise typer.Exit(code=2)
    else:
        echo_success("All files valid")


@app.command()
def images(
    file: Annotated[
        Path,
        typer.Argument(
            help="Harness YAML file to resolve images for.",
            exists=True,
            dir_okay=False,
        ),
    ],
    scrape: Annotated[
        bool,
        typer.Option("--scrape", help="Enable web scraping for missing images."),
    ] = False,
    cache_dir: Annotated[
        Path,
        typer.Option("--cache-dir", help="Directory for cached images."),
    ] = Path("assets/images"),
    ci: Annotated[
        bool,
        typer.Option("--ci", help="CI mode: fail if any images would require scraping."),
    ] = False,
) -> None:
    """
    Resolve and download part images.

    Images are resolved in order:
    1. Explicit path in YAML
    2. Local file: <Manufacturer>_<MPN>.(png|jpg)
    3. Local file: <PN>.(png|jpg)
    4. Web scraping (if --scrape enabled)

    [bold]Examples:[/bold]

        wvdoc images harness.yml

        wvdoc images harness.yml --scrape

        wvdoc images harness.yml --ci
    """
    echo_header("WireViz Doc Images")
    echo_info(f"Resolving images for {file.name}")
    echo_debug(f"Cache directory: {cache_dir}")

    if ci and scrape:
        echo_error("Cannot use --scrape with --ci mode")
        raise typer.Exit(code=1)

    if scrape:
        echo_warning("Web scraping enabled - images will be downloaded")
    elif ci:
        echo_info("CI mode - scraping disabled, will fail on missing images")

    # TODO: Implement image resolution
    echo_warning("Image resolution not yet implemented")

    rprint()
    echo_info("Image resolution complete")


if __name__ == "__main__":
    app()
