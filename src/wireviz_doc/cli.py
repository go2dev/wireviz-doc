"""CLI interface for wireviz-doc."""

import shutil
import sys

import typer

app = typer.Typer(
    name="wvdoc",
    help="WireViz-based harness documentation pipeline for generating factory-ready wiring documentation.",
)


def check_graphviz() -> bool:
    """Check if graphviz (dot) is available on the system."""
    return shutil.which("dot") is not None


@app.callback()
def main() -> None:
    """WireViz documentation generator CLI."""
    if not check_graphviz():
        typer.secho(
            "Warning: Graphviz (dot) not found. Some features may not work correctly.",
            fg=typer.colors.YELLOW,
            err=True,
        )


@app.command()
def build() -> None:
    """Build documentation from WireViz YAML files."""
    typer.echo("Not implemented yet")


@app.command()
def images() -> None:
    """Generate images from WireViz definitions."""
    typer.echo("Not implemented yet")


@app.command()
def lint() -> None:
    """Lint WireViz YAML files for errors and best practices."""
    typer.echo("Not implemented yet")


if __name__ == "__main__":
    app()
