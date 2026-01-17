#!/usr/bin/env python3
"""
Example data and test script for WireViz SVG templates.

This script demonstrates how to render the SVG templates with sample data.
Run this script to generate example SVG outputs for testing.

Usage:
    python example_data.py

Output:
    - example_sheet.svg
    - example_bom.svg
    - example_wiring.svg
    - example_title_block.svg
"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# Sample metadata for title block
EXAMPLE_METADATA = {
    "id": "WH-2024-001",
    "title": "Main Control Panel Wiring Harness",
    "revision": "B",
    "date": "2024-01-15",
    "author": "J. Smith",
    "checker": "M. Johnson",
    "approver": "R. Williams",
    "project": "Industrial Controller v2.0",
    "company": "ACME Electronics",
    "sheet": 1,
    "total_sheets": 2,
    "scale": "NTS",
    "units": "mm",
    "description": "Primary wiring harness for main control panel assembly. Includes power, signal, and communication connections."
}

# Sample BOM data
EXAMPLE_BOM = [
    {
        "item": 1,
        "part_number": "CON-DB9-M",
        "manufacturer": "TE Connectivity",
        "mpn": "5747840-4",
        "description": "D-Sub Connector, 9 Pin, Male",
        "qty": 2,
        "alternates": "Amphenol ICC 17EHH009SAA"
    },
    {
        "item": 2,
        "part_number": "CON-DB9-F",
        "manufacturer": "TE Connectivity",
        "mpn": "5747840-5",
        "description": "D-Sub Connector, 9 Pin, Female",
        "qty": 1,
        "alternates": ""
    },
    {
        "item": 3,
        "part_number": "CBL-22AWG-4C",
        "manufacturer": "Alpha Wire",
        "mpn": "5474C SL001",
        "description": "Shielded Cable, 22AWG, 4 Conductor",
        "qty": "2.5m",
        "alternates": "Belden 8723"
    },
    {
        "item": 4,
        "part_number": "CBL-18AWG-2C",
        "manufacturer": "Alpha Wire",
        "mpn": "5072C SL001",
        "description": "Power Cable, 18AWG, 2 Conductor",
        "qty": "1.8m",
        "alternates": ""
    },
    {
        "item": 5,
        "part_number": "TERM-RING-22",
        "manufacturer": "Molex",
        "mpn": "19164-0042",
        "description": "Ring Terminal, 22-18AWG, #6 Stud",
        "qty": 8,
        "alternates": "TE 34148"
    },
    {
        "item": 6,
        "part_number": "SHRINK-3MM-BK",
        "manufacturer": "3M",
        "mpn": "FP-301-3/32",
        "description": "Heat Shrink Tubing, 3mm, Black",
        "qty": "0.5m",
        "alternates": ""
    },
    {
        "item": 7,
        "part_number": "LABEL-WHT-SM",
        "manufacturer": "Brady",
        "mpn": "PTL-19-427",
        "description": "Wire Label, White, Self-Laminating",
        "qty": 12,
        "alternates": "Panduit S100X150YAJ"
    }
]

# Sample wiring data
EXAMPLE_WIRING = [
    {
        "from_component": "J1",
        "from_pin": "1",
        "to_component": "TB1",
        "to_pin": "1",
        "cable": "W1",
        "core": "1",
        "label": "PWR+",
        "color": "RD",
        "pair": "",
        "notes": "Main power supply positive"
    },
    {
        "from_component": "J1",
        "from_pin": "2",
        "to_component": "TB1",
        "to_pin": "2",
        "cable": "W1",
        "core": "2",
        "label": "PWR-",
        "color": "BK",
        "pair": "",
        "notes": "Main power supply return"
    },
    {
        "from_component": "J2",
        "from_pin": "1",
        "to_component": "J3",
        "to_pin": "1",
        "cable": "W2",
        "core": "1",
        "label": "TX+",
        "color": "WH",
        "pair": "1",
        "notes": "RS-485 transmit positive"
    },
    {
        "from_component": "J2",
        "from_pin": "2",
        "to_component": "J3",
        "to_pin": "2",
        "cable": "W2",
        "core": "2",
        "label": "TX-",
        "color": "BU",
        "pair": "1",
        "notes": "RS-485 transmit negative"
    },
    {
        "from_component": "J2",
        "from_pin": "3",
        "to_component": "J3",
        "to_pin": "3",
        "cable": "W2",
        "core": "3",
        "label": "RX+",
        "color": "OR",
        "pair": "2",
        "notes": "RS-485 receive positive"
    },
    {
        "from_component": "J2",
        "from_pin": "4",
        "to_component": "J3",
        "to_pin": "4",
        "cable": "W2",
        "core": "4",
        "label": "RX-",
        "color": "GN",
        "pair": "2",
        "notes": "RS-485 receive negative"
    },
    {
        "from_component": "J2",
        "from_pin": "5",
        "to_component": "TB2",
        "to_pin": "1",
        "cable": "W2",
        "core": "SH",
        "label": "SHLD",
        "color": "GY",
        "pair": "",
        "notes": "Cable shield drain wire"
    },
    {
        "from_component": "J4",
        "from_pin": "A",
        "to_component": "SW1",
        "to_pin": "1",
        "cable": "W3",
        "core": "1",
        "label": "SIG1",
        "color": "YE",
        "pair": "",
        "notes": "Digital input 1"
    },
    {
        "from_component": "J4",
        "from_pin": "B",
        "to_component": "SW1",
        "to_pin": "2",
        "cable": "W3",
        "core": "2",
        "label": "SIG2",
        "color": "VT",
        "pair": "",
        "notes": "Digital input 2"
    }
]

# Sample notes
EXAMPLE_NOTES = [
    "All connections to be crimped using approved tooling.",
    "Apply heat shrink tubing to all exposed terminals.",
    "Cable routing per installation drawing DWG-2024-002.",
    "Refer to test procedure TP-2024-001 for continuity testing."
]


def render_templates():
    """Render all templates with example data."""
    template_dir = Path(__file__).parent
    output_dir = template_dir / "examples"
    output_dir.mkdir(exist_ok=True)

    env = Environment(loader=FileSystemLoader(str(template_dir)))

    # Render sheet template
    print("Rendering sheet-a4.svg.j2...")
    template = env.get_template("sheet-a4.svg.j2")
    output = template.render(
        metadata=EXAMPLE_METADATA,
        bom=EXAMPLE_BOM,
        notes=EXAMPLE_NOTES,
        page_type="diagram",
        show_bom=True
    )
    (output_dir / "example_sheet.svg").write_text(output)
    print(f"  -> {output_dir / 'example_sheet.svg'}")

    # Render BOM table
    print("Rendering bom-table.svg.j2...")
    template = env.get_template("bom-table.svg.j2")
    output = template.render(bom=EXAMPLE_BOM)
    (output_dir / "example_bom.svg").write_text(output)
    print(f"  -> {output_dir / 'example_bom.svg'}")

    # Render wiring table
    print("Rendering wiring-table.svg.j2...")
    template = env.get_template("wiring-table.svg.j2")
    output = template.render(wiring=EXAMPLE_WIRING)
    (output_dir / "example_wiring.svg").write_text(output)
    print(f"  -> {output_dir / 'example_wiring.svg'}")

    # Render title block
    print("Rendering title-block.svg.j2...")
    template = env.get_template("title-block.svg.j2")
    output = template.render(metadata=EXAMPLE_METADATA)
    (output_dir / "example_title_block.svg").write_text(output)
    print(f"  -> {output_dir / 'example_title_block.svg'}")

    print("\nAll templates rendered successfully!")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    render_templates()
