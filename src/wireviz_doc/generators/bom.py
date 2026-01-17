"""
Bill of Materials (BOM) generation module.

Extracts all parts from a HarnessDocument and generates a complete BOM
including connectors, cables, accessories, and their alternates.

Output formats: TSV, HTML, and structured data for SVG embedding.

Columns:
- Item: Line item number
- Qty: Quantity required
- Unit: Unit of measure
- PN: Part number (primary)
- Manufacturer: Manufacturer name
- MPN: Manufacturer part number
- Description: Part description
- Alternates: Alternative part numbers (comma-separated)

Usage:
    from wireviz_doc.generators.bom import generate_bom_tsv

    tsv_content = generate_bom_tsv(document)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from wireviz_doc.models.document import HarnessDocument
from wireviz_doc.output import logger


@dataclass
class BOMItem:
    """Represents a single line item in the BOM."""

    item_number: int
    quantity: float
    unit: str
    part_number: str
    manufacturer: str
    mpn: str
    description: str
    alternates: List[str] = field(default_factory=list)
    category: str = ""  # connector, cable, accessory, etc.
    reference: str = ""  # Reference designator (J1, W1, etc.)


# Column headers for BOM
BOM_HEADERS = [
    "Item",
    "Qty",
    "Unit",
    "Reference",
    "PN",
    "Manufacturer",
    "MPN",
    "Description",
    "Alternates",
]


def _extract_bom_items(document: HarnessDocument) -> List[BOMItem]:
    """
    Extract all BOM items from a HarnessDocument.

    Items are deduplicated by part number and quantities are summed.
    """
    # Track items by primary PN for deduplication
    items_by_pn: Dict[str, Dict[str, Any]] = {}

    # Process connectors
    for conn_id, connector in document.connectors.items():
        pn = connector.primary_pn

        if pn not in items_by_pn:
            alternates = [f"{alt.manufacturer} {alt.mpn}" for alt in connector.alternates]
            items_by_pn[pn] = {
                "quantity": 0,
                "unit": "pcs",
                "manufacturer": connector.manufacturer,
                "mpn": connector.mpn,
                "description": connector.description,
                "alternates": alternates,
                "category": "connector",
                "references": [],
            }

        items_by_pn[pn]["quantity"] += 1
        items_by_pn[pn]["references"].append(conn_id)

    # Process cables
    for cable_id, cable in document.cables.items():
        pn = cable.primary_pn

        if pn not in items_by_pn:
            alternates = [f"{alt.manufacturer} {alt.mpn}" for alt in cable.alternates]
            items_by_pn[pn] = {
                "quantity": 0.0,
                "unit": cable.length.unit if cable.length else "pcs",
                "manufacturer": cable.manufacturer,
                "mpn": cable.mpn,
                "description": cable.description,
                "alternates": alternates,
                "category": "cable",
                "references": [],
            }

        # Add length to quantity
        if cable.length:
            items_by_pn[pn]["quantity"] += cable.length.value
        else:
            items_by_pn[pn]["quantity"] += 1

        items_by_pn[pn]["references"].append(cable_id)

    # Process accessories
    for accessory in document.accessories:
        part = accessory.part
        pn = part.primary_pn

        if pn not in items_by_pn:
            alternates = [f"{alt.manufacturer} {alt.mpn}" for alt in part.alternates]
            items_by_pn[pn] = {
                "quantity": 0.0,
                "unit": accessory.quantity.unit,
                "manufacturer": part.manufacturer,
                "mpn": part.mpn,
                "description": part.description,
                "alternates": alternates,
                "category": "accessory",
                "references": [],
            }

        items_by_pn[pn]["quantity"] += accessory.quantity.value

    # Process generic parts
    for part_id, part in document.parts.items():
        pn = part.primary_pn

        # Skip if already added via connectors/cables
        if pn in items_by_pn:
            continue

        alternates = [f"{alt.manufacturer} {alt.mpn}" for alt in part.alternates]
        items_by_pn[pn] = {
            "quantity": 1,
            "unit": "pcs",
            "manufacturer": part.manufacturer,
            "mpn": part.mpn,
            "description": part.description,
            "alternates": alternates,
            "category": "part",
            "references": [part_id],
        }

    # Convert to BOMItem list
    bom_items = []
    for idx, (pn, data) in enumerate(sorted(items_by_pn.items()), start=1):
        bom_items.append(BOMItem(
            item_number=idx,
            quantity=data["quantity"],
            unit=data["unit"],
            part_number=pn,
            manufacturer=data["manufacturer"],
            mpn=data["mpn"],
            description=data["description"],
            alternates=data["alternates"],
            category=data["category"],
            reference=", ".join(data["references"]),
        ))

    return bom_items


def generate_bom_tsv(document: HarnessDocument) -> str:
    """
    Generate BOM as TSV (Tab-Separated Values).

    Args:
        document: The HarnessDocument.

    Returns:
        TSV content as a string.

    Example:
        >>> tsv = generate_bom_tsv(document)
        >>> with open("bom.tsv", "w") as f:
        ...     f.write(tsv)
    """
    items = _extract_bom_items(document)

    lines = []

    # Header row
    lines.append("\t".join(BOM_HEADERS))

    # Data rows
    for item in items:
        # Format quantity - remove trailing zeros for integers
        if item.quantity == int(item.quantity):
            qty_str = str(int(item.quantity))
        else:
            qty_str = f"{item.quantity:.2f}"

        alternates_str = "; ".join(item.alternates) if item.alternates else ""

        line = "\t".join([
            str(item.item_number),
            qty_str,
            item.unit,
            item.reference,
            item.part_number,
            item.manufacturer,
            item.mpn,
            item.description,
            alternates_str,
        ])
        lines.append(line)

    return "\n".join(lines)


def generate_bom_tsv_file(
    document: HarnessDocument,
    output_path: Union[str, Path],
) -> Path:
    """
    Generate BOM TSV file.

    Args:
        document: The HarnessDocument.
        output_path: Path for the output file.

    Returns:
        Path to the generated file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = generate_bom_tsv(document)

    logger.info(f"Writing BOM to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    items = _extract_bom_items(document)
    logger.debug(f"Generated BOM with {len(items)} line items")

    return output_path


def generate_bom_html(
    document: HarnessDocument,
    include_styles: bool = True,
) -> str:
    """
    Generate BOM as HTML table.

    Args:
        document: The HarnessDocument.
        include_styles: Whether to include inline CSS.

    Returns:
        HTML table as a string.
    """
    items = _extract_bom_items(document)

    parts = []

    if include_styles:
        parts.append("""<style>
.bom-table {
    border-collapse: collapse;
    font-family: Arial, sans-serif;
    font-size: 10px;
    width: 100%;
}
.bom-table th {
    background-color: #2c3e50;
    color: white;
    padding: 5px 8px;
    text-align: left;
    border: 1px solid #1a252f;
    font-weight: bold;
}
.bom-table td {
    padding: 4px 8px;
    border: 1px solid #ddd;
}
.bom-table tr:nth-child(even) {
    background-color: #f9f9f9;
}
.bom-table tr:hover {
    background-color: #e8f4f8;
}
.bom-table .item-num {
    text-align: center;
    font-weight: bold;
}
.bom-table .qty {
    text-align: right;
    font-weight: bold;
}
.bom-table .pn {
    font-family: monospace;
    font-weight: bold;
    color: #1a5276;
}
.bom-table .mpn {
    font-family: monospace;
    color: #666;
}
.bom-table .alternates {
    font-size: 9px;
    color: #777;
    font-style: italic;
}
</style>
""")

    parts.append('<table class="bom-table">')

    # Header row
    parts.append("<thead><tr>")
    for header in BOM_HEADERS:
        parts.append(f"<th>{_escape_html(header)}</th>")
    parts.append("</tr></thead>")

    # Data rows
    parts.append("<tbody>")
    for item in items:
        # Format quantity
        if item.quantity == int(item.quantity):
            qty_str = str(int(item.quantity))
        else:
            qty_str = f"{item.quantity:.2f}"

        alternates_str = "; ".join(item.alternates) if item.alternates else "-"

        parts.append("<tr>")
        parts.append(f'<td class="item-num">{item.item_number}</td>')
        parts.append(f'<td class="qty">{qty_str}</td>')
        parts.append(f"<td>{_escape_html(item.unit)}</td>")
        parts.append(f"<td>{_escape_html(item.reference)}</td>")
        parts.append(f'<td class="pn">{_escape_html(item.part_number)}</td>')
        parts.append(f"<td>{_escape_html(item.manufacturer)}</td>")
        parts.append(f'<td class="mpn">{_escape_html(item.mpn)}</td>')
        parts.append(f"<td>{_escape_html(item.description)}</td>")
        parts.append(f'<td class="alternates">{_escape_html(alternates_str)}</td>')
        parts.append("</tr>")
    parts.append("</tbody>")

    parts.append("</table>")

    return "\n".join(parts)


def generate_bom_svg_snippet(
    document: HarnessDocument,
    x: float = 0,
    y: float = 0,
    max_width: float = 280,
    row_height: float = 4,
) -> str:
    """
    Generate BOM as SVG elements for direct embedding.

    Args:
        document: The HarnessDocument.
        x: X offset for the table.
        y: Y offset for the table.
        max_width: Maximum table width.
        row_height: Height of each row.

    Returns:
        SVG elements as a string.
    """
    items = _extract_bom_items(document)

    # Compact headers for SVG
    compact_headers = ["#", "Qty", "Unit", "Ref", "PN", "Mfr", "MPN", "Description"]
    col_widths = [8, 12, 12, 20, 35, 35, 40, 60]  # mm widths

    parts = []
    parts.append(f'<g id="bom-table" transform="translate({x}, {y})">')

    # Styles
    parts.append("""<style type="text/css">
    .bom-header { font-family: Arial; font-size: 2.2px; font-weight: bold; fill: white; }
    .bom-cell { font-family: Arial; font-size: 2px; fill: #333; }
    .bom-header-bg { fill: #2c3e50; }
    .bom-row-even { fill: #f9f9f9; }
    .bom-row-odd { fill: white; }
    .bom-border { stroke: #ddd; stroke-width: 0.1; fill: none; }
    </style>""")

    total_width = sum(col_widths)

    # Header row
    current_x = 0
    parts.append(f'<rect x="0" y="0" width="{total_width}" height="{row_height}" class="bom-header-bg"/>')

    for header, width in zip(compact_headers, col_widths):
        text_x = current_x + 1
        text_y = row_height * 0.7
        parts.append(f'<text x="{text_x}" y="{text_y}" class="bom-header">{header}</text>')
        current_x += width

    # Data rows
    current_y = row_height
    for row_idx, item in enumerate(items):
        # Row background
        bg_class = "bom-row-even" if row_idx % 2 == 0 else "bom-row-odd"
        parts.append(f'<rect x="0" y="{current_y}" width="{total_width}" height="{row_height}" class="{bg_class}"/>')

        # Format quantity
        if item.quantity == int(item.quantity):
            qty_str = str(int(item.quantity))
        else:
            qty_str = f"{item.quantity:.1f}"

        # Cell values (compact)
        values = [
            str(item.item_number),
            qty_str,
            item.unit,
            item.reference[:8],  # Truncate
            item.part_number[:12],
            item.manufacturer[:12],
            item.mpn[:15],
            item.description[:25],
        ]

        current_x = 0
        for value, width in zip(values, col_widths):
            text_x = current_x + 1
            text_y = current_y + row_height * 0.7
            parts.append(f'<text x="{text_x}" y="{text_y}" class="bom-cell">{_escape_xml(value)}</text>')
            current_x += width

        current_y += row_height

    # Table border
    parts.append(f'<rect x="0" y="0" width="{total_width}" height="{current_y}" class="bom-border"/>')

    parts.append('</g>')

    return "\n".join(parts)


def get_bom_data(document: HarnessDocument) -> List[Dict[str, Any]]:
    """
    Get BOM data as a list of dictionaries.

    Useful for template rendering or API responses.

    Args:
        document: The HarnessDocument.

    Returns:
        List of dictionaries with BOM data.
    """
    items = _extract_bom_items(document)

    result = []
    for item in items:
        result.append({
            "item": item.item_number,
            "qty": item.quantity,
            "unit": item.unit,
            "reference": item.reference,
            "pn": item.part_number,
            "manufacturer": item.manufacturer,
            "mpn": item.mpn,
            "description": item.description,
            "alternates": item.alternates,
            "category": item.category,
        })

    return result


def _escape_html(text: str) -> str:
    """Escape special HTML characters."""
    if not text:
        return ""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _escape_xml(text: str) -> str:
    """Escape special XML characters for SVG."""
    if not text:
        return ""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("'", "&apos;")
            .replace('"', "&quot;"))
