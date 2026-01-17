"""
CLI interface for WireViz Doc.

Provides the `wvdoc` command with subcommands for building documentation,
resolving images, and linting harness YAML files.
"""

from __future__ import annotations

import shutil
import subprocess
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


def check_wireviz() -> bool:
    """Check if WireViz is available."""
    return shutil.which("wireviz") is not None


def check_cairosvg() -> bool:
    """Check if CairoSVG is available."""
    try:
        import cairosvg
        return True
    except ImportError:
        return False


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


def echo_step(step: int, total: int, message: str) -> None:
    """Print build step message."""
    if not _quiet:
        rprint(f"  [dim][{step}/{total}][/dim] {message}")


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


def build_single_harness(
    harness_file: Path,
    harness_output_dir: Path,
    template: Optional[Path],
    format: str,
    allow_missing_images: bool,
    ci: bool,
) -> tuple[int, int]:
    """
    Build a single harness file.

    Returns tuple of (errors, warnings).
    """
    from wireviz_doc.composers.svg_composer import (
        compose_svg_from_template,
        get_template_path,
    )
    from wireviz_doc.generators.bom import generate_bom_tsv_file, get_bom_data
    from wireviz_doc.generators.wiring_table import generate_wiring_table_tsv_file
    from wireviz_doc.parser import ParserError, parse_harness_yaml
    from wireviz_doc.resolvers.images import get_missing_images, resolve_images

    errors = 0
    warnings = 0
    total_steps = 8

    try:
        # Step 1: Parse extended YAML
        echo_step(1, total_steps, "Parsing YAML...")
        try:
            document = parse_harness_yaml(harness_file)
            logger.info(f"Parsed document: {document.metadata.id}")
        except ParserError as e:
            echo_error(f"Parse error: {e.message}")
            for detail in e.details:
                echo_error(f"  {detail}")
            return (1, 0)

        # Use the document ID for naming (may differ from filename)
        harness_id = document.metadata.id
        echo_debug(f"Document ID: {harness_id}")

        # Step 2: Validate schema
        echo_step(2, total_steps, "Validating schema...")
        validation_issues = document.validate_complete()
        for issue in validation_issues:
            echo_warning(f"Validation: {issue}")
            warnings += 1
            logger.warning(issue)

        # Step 3: Resolve images
        echo_step(3, total_steps, "Resolving images...")
        search_dirs = [
            harness_file.parent / "images",
            harness_file.parent / "assets" / "images",
            Path("assets/images"),
            Path("images"),
        ]
        image_paths = resolve_images(
            document,
            search_dirs=[d for d in search_dirs if d.exists()],
            base_path=harness_file.parent,
        )

        if image_paths:
            echo_debug(f"Resolved {len(image_paths)} images")

        missing_images = get_missing_images(
            document,
            search_dirs=[d for d in search_dirs if d.exists()],
            base_path=harness_file.parent,
        )
        if missing_images:
            for img in missing_images:
                msg = f"Missing image: {img['type']} {img['id']} ({img['suggested_filename']})"
                if allow_missing_images:
                    echo_warning(msg)
                    warnings += 1
                else:
                    echo_warning(msg)
                    warnings += 1

        # Step 4: Run WireViz directly on input file
        # The input YAML is WireViz-compatible (WireViz ignores our extended sections)
        echo_step(4, total_steps, "Running WireViz...")
        wireviz_output_dir = harness_output_dir / "wireviz"
        wireviz_output_dir.mkdir(parents=True, exist_ok=True)

        if check_wireviz():
            try:
                result = subprocess.run(
                    ["wireviz", str(harness_file), "-o", str(wireviz_output_dir)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if result.returncode != 0:
                    # WireViz may output warnings to stderr even on success
                    stderr_lines = result.stderr.strip().split('\n') if result.stderr else []
                    for line in stderr_lines:
                        if line and not line.startswith('WireViz'):
                            echo_warning(f"WireViz: {line}")
                            logger.warning(f"WireViz: {line}")
                    warnings += len([l for l in stderr_lines if l and 'Unknown color' in l])
                echo_debug("WireViz completed")
                logger.info("WireViz completed")
            except subprocess.TimeoutExpired:
                echo_error("WireViz timed out")
                errors += 1
            except Exception as e:
                echo_error(f"WireViz error: {e}")
                errors += 1
        else:
            echo_warning("WireViz not installed - skipping diagram generation")
            warnings += 1

        # Find WireViz output SVG
        diagram_svg_path = None
        wireviz_svg_candidates = list(wireviz_output_dir.glob("*.svg"))
        if wireviz_svg_candidates:
            diagram_svg_path = wireviz_svg_candidates[0]
            echo_debug(f"WireViz SVG: {diagram_svg_path}")

        # Step 5: Copy source YAML to output for reference
        echo_step(5, total_steps, "Copying source YAML...")
        source_yaml_copy = harness_output_dir / "source.yml"
        shutil.copy(harness_file, source_yaml_copy)
        echo_debug(f"Source YAML copied to: {source_yaml_copy}")

        # Step 6: Generate wiring table
        echo_step(6, total_steps, "Generating wiring table...")
        wiring_table_path = harness_output_dir / "wiring_table.tsv"
        generate_wiring_table_tsv_file(document, wiring_table_path)
        echo_file_created(wiring_table_path)

        # Step 7: Generate BOM
        echo_step(7, total_steps, "Generating BOM...")
        bom_path = harness_output_dir / "bom.tsv"
        generate_bom_tsv_file(document, bom_path)
        echo_file_created(bom_path)

        # Step 8: Compose final SVG and convert to PDF
        echo_step(8, total_steps, "Composing final output...")

        # Get template path
        if template:
            template_path = template
        else:
            try:
                template_path = get_template_path("sheet-a4.svg.j2")
            except FileNotFoundError:
                echo_warning("Default template not found, using diagram SVG directly")
                template_path = None

        # Compose SVG
        final_svg_path = harness_output_dir / "diagram.svg"

        if template_path and diagram_svg_path and diagram_svg_path.exists():
            diagram_svg_content = diagram_svg_path.read_text()
            bom_data = get_bom_data(document)

            final_svg = compose_svg_from_template(
                template_path=template_path,
                diagram_svg=diagram_svg_content,
                metadata=document.metadata,
                bom_data=bom_data,
                page_type="diagram",
            )
            final_svg_path.write_text(final_svg)
            echo_file_created(final_svg_path)
        elif diagram_svg_path and diagram_svg_path.exists():
            # Copy WireViz output as final SVG
            shutil.copy(diagram_svg_path, final_svg_path)
            echo_file_created(final_svg_path)
        else:
            echo_warning("No diagram SVG generated")

        # Convert to PDF if requested
        if format in ("pdf", "all"):
            pdf_path = harness_output_dir / "diagram.pdf"
            if check_cairosvg() and final_svg_path.exists():
                try:
                    import cairosvg
                    cairosvg.svg2pdf(
                        url=str(final_svg_path),
                        write_to=str(pdf_path),
                    )
                    echo_file_created(pdf_path)
                except Exception as e:
                    echo_warning(f"PDF conversion failed: {e}")
                    warnings += 1
            else:
                if not check_cairosvg():
                    echo_warning("CairoSVG not installed - skipping PDF generation")
                warnings += 1

        # Also keep the raw WireViz outputs if they exist
        if diagram_svg_path and diagram_svg_path.exists() and diagram_svg_path != final_svg_path:
            echo_debug(f"WireViz SVG: {diagram_svg_path}")

        return (errors, warnings)

    except Exception as e:
        echo_error(f"Build failed: {e}")
        logger.exception("Build failed with exception")
        return (1, warnings)


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

    total_errors = 0
    total_warnings = 0
    built_harnesses: list[tuple[Path, str]] = []

    for harness_file in expanded_files:
        rprint(f"\n[bold cyan]▸ Processing {harness_file.name}[/bold cyan]")

        # Determine harness ID (from filename initially, may be updated from YAML)
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

        # Build the harness
        errors, warnings = build_single_harness(
            harness_file=harness_file,
            harness_output_dir=harness_output_dir,
            template=template,
            format=format,
            allow_missing_images=allow_missing_images,
            ci=ci,
        )

        total_errors += errors
        total_warnings += warnings
        built_harnesses.append((harness_file, harness_id))

        if log_file:
            logger.info(f"Build complete: {errors} errors, {warnings} warnings")
            close_file_logging()

    elapsed = (datetime.now() - start_time).total_seconds()

    # Summary
    rprint()
    if total_errors > 0:
        rprint("[red bold]BUILD FAILED[/red bold]")
    elif total_warnings > 0:
        rprint("[yellow]BUILD COMPLETE (with warnings)[/yellow]")
    else:
        rprint("[green bold]BUILD COMPLETE[/green bold]")

    # Show output tree
    if not _quiet:
        rprint()
        tree = Tree(f"[blue]{output_dir}[/blue]")
        for harness_file, harness_id in built_harnesses:
            branch = tree.add(f"[blue]{harness_id}/[/blue]")
            branch.add("[dim]diagram.svg[/dim]")
            if format in ("pdf", "all"):
                branch.add("[dim]diagram.pdf[/dim]")
            branch.add("[dim]bom.tsv[/dim]")
            branch.add("[dim]wiring_table.tsv[/dim]")
            branch.add("[dim]source.yml[/dim]")
            branch.add("[dim]wireviz/[/dim] (WireViz outputs)")
            if log_file:
                branch.add("[dim]build.log[/dim]")
        rprint(tree)

    rprint(f"\n[dim]Completed in {elapsed:.2f}s[/dim]")

    if total_errors > 0:
        raise typer.Exit(code=1)
    elif total_warnings > 0:
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
    from wireviz_doc.parser import ParserError, validate_harness_yaml

    echo_header("WireViz Doc Lint")

    total_errors = 0
    total_warnings = 0

    for harness_file in files:
        if not harness_file.exists():
            echo_error(f"File not found: {harness_file}")
            total_errors += 1
            continue

        rprint(f"\n[bold cyan]▸ Validating {harness_file.name}[/bold cyan]")

        # Validate using the parser
        issues = validate_harness_yaml(harness_file)

        errors: list[str] = []
        warnings: list[str] = []

        for issue in issues:
            # Determine if error or warning based on content
            if "error" in issue.lower() or "not found" in issue.lower():
                errors.append(issue)
            else:
                warnings.append(issue)

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
    from wireviz_doc.parser import ParserError, parse_harness_yaml
    from wireviz_doc.resolvers.images import get_missing_images, resolve_images

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

    # Parse the document
    try:
        document = parse_harness_yaml(file)
    except ParserError as e:
        echo_error(f"Parse error: {e.message}")
        raise typer.Exit(code=1)

    # Resolve images
    search_dirs = [
        file.parent / "images",
        file.parent / "assets" / "images",
        cache_dir,
        Path("images"),
    ]

    resolved = resolve_images(
        document,
        search_dirs=[d for d in search_dirs if d.exists()],
        base_path=file.parent,
    )

    missing = get_missing_images(
        document,
        search_dirs=[d for d in search_dirs if d.exists()],
        base_path=file.parent,
    )

    # Report results
    if resolved:
        echo_success(f"Found {len(resolved)} images:")
        for component_id, path in resolved.items():
            rprint(f"  [green]✓[/green] {component_id}: {path}")

    if missing:
        rprint()
        echo_warning(f"Missing {len(missing)} images:")
        for img in missing:
            rprint(f"  [yellow]?[/yellow] {img['type']} {img['id']}: {img['suggested_filename']}")

        if ci:
            echo_error("CI mode: failing due to missing images")
            raise typer.Exit(code=1)

    rprint()
    echo_info("Image resolution complete")

    if missing and not scrape:
        echo_info(f"Tip: Place missing images in {cache_dir}")


if __name__ == "__main__":
    app()
