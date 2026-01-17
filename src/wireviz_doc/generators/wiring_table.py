"""
Wiring table generation module.

Generates wiring tables from HarnessDocument connections.
Output formats: TSV (for external tools) and HTML (for SVG embedding).

Columns:
- From: Source connector ID
- From Pin: Source pin number/label
- To: Destination connector ID
- To Pin: Destination pin number/label
- Cable: Cable ID
- Core: Core index (1-based)
- Label: Wire label
- Color: Wire color code
- Pair Group: Twisted pair group (if applicable)
- Notes: Connection notes

Usage:
    from wireviz_doc.generators.wiring_table import generate_wiring_table_tsv

    tsv_content = generate_wiring_table_tsv(document)
    html_content = generate_wiring_table_html(document)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from wireviz_doc.models.document import HarnessDocument
from wireviz_doc.output import logger


@dataclass
class WiringTableRow:
    """Represents a single row in the wiring table."""

    from_connector: str
    from_pin: str
    to_connector: str
    to_pin: str
    cable: str
    core: int  # 1-based for display
    label: str
    color: str
    pair_group: str
    notes: str


# Column headers for the wiring table
WIRING_TABLE_HEADERS = [
    "From",
    "From Pin",
    "To",
    "To Pin",
    "Cable",
    "Core",
    "Label",
    "Color",
    "Pair Group",
    "Notes",
]


def _build_wiring_table_rows(document: HarnessDocument) -> List[WiringTableRow]:
    """
    Build wiring table rows from document connections.

    Args:
        document: The HarnessDocument containing connections.

    Returns:
        List of WiringTableRow objects.
    """
    rows = []

    for conn in document.connections:
        # Get cable and core info
        cable = document.cables.get(conn.cable)

        # Default values
        label = ""
        color = ""
        pair_group = ""

        if cable and cable.cores:
            # Find core by index (0-based internal)
            for core in cable.cores:
                if core.index == conn.core:
                    label = core.label or ""
                    color = core.color.display_color
                    pair_group = core.pair_group or ""
                    break

        # Use wire_label override if provided
        if conn.wire_label:
            label = conn.wire_label

        # Use signal_name as label if no core label
        if not label and conn.signal_name:
            label = conn.signal_name

        rows.append(WiringTableRow(
            from_connector=conn.from_connector,
            from_pin=str(conn.from_pin),
            to_connector=conn.to_connector,
            to_pin=str(conn.to_pin),
            cable=conn.cable,
            core=conn.core + 1,  # Convert to 1-based for display
            label=label,
            color=color,
            pair_group=pair_group,
            notes=conn.notes or "",
        ))

    return rows


def generate_wiring_table_tsv(document: HarnessDocument) -> str:
    """
    Generate wiring table as TSV (Tab-Separated Values).

    Args:
        document: The HarnessDocument.

    Returns:
        TSV content as a string.

    Example:
        >>> tsv = generate_wiring_table_tsv(document)
        >>> with open("wiring_table.tsv", "w") as f:
        ...     f.write(tsv)
    """
    rows = _build_wiring_table_rows(document)

    lines = []

    # Header row
    lines.append("\t".join(WIRING_TABLE_HEADERS))

    # Data rows
    for row in rows:
        line = "\t".join([
            row.from_connector,
            row.from_pin,
            row.to_connector,
            row.to_pin,
            row.cable,
            str(row.core),
            row.label,
            row.color,
            row.pair_group,
            row.notes,
        ])
        lines.append(line)

    return "\n".join(lines)


def generate_wiring_table_tsv_file(
    document: HarnessDocument,
    output_path: Union[str, Path],
) -> Path:
    """
    Generate wiring table TSV file.

    Args:
        document: The HarnessDocument.
        output_path: Path for the output file.

    Returns:
        Path to the generated file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = generate_wiring_table_tsv(document)

    logger.info(f"Writing wiring table to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.debug(f"Generated wiring table with {len(document.connections)} rows")
    return output_path


def generate_wiring_table_html(
    document: HarnessDocument,
    include_styles: bool = True,
) -> str:
    """
    Generate wiring table as HTML for embedding in SVG.

    Args:
        document: The HarnessDocument.
        include_styles: Whether to include inline CSS styles.

    Returns:
        HTML table as a string.

    Example:
        >>> html = generate_wiring_table_html(document)
    """
    rows = _build_wiring_table_rows(document)

    # Build HTML table
    parts = []

    if include_styles:
        parts.append("""<style>
.wiring-table {
    border-collapse: collapse;
    font-family: Arial, sans-serif;
    font-size: 10px;
    width: 100%;
}
.wiring-table th {
    background-color: #4a4a4a;
    color: white;
    padding: 4px 6px;
    text-align: left;
    border: 1px solid #333;
    font-weight: bold;
}
.wiring-table td {
    padding: 3px 6px;
    border: 1px solid #ccc;
}
.wiring-table tr:nth-child(even) {
    background-color: #f5f5f5;
}
.wiring-table tr:hover {
    background-color: #e8f4f8;
}
.wiring-table .connector-cell {
    font-weight: bold;
    color: #1a5276;
}
.wiring-table .cable-cell {
    color: #7d3c98;
}
.wiring-table .color-cell {
    font-family: monospace;
    font-weight: bold;
}
.wiring-table .notes-cell {
    font-style: italic;
    color: #666;
}
</style>
""")

    parts.append('<table class="wiring-table">')

    # Header row
    parts.append("<thead><tr>")
    for header in WIRING_TABLE_HEADERS:
        parts.append(f"<th>{_escape_html(header)}</th>")
    parts.append("</tr></thead>")

    # Data rows
    parts.append("<tbody>")
    for row in rows:
        parts.append("<tr>")
        parts.append(f'<td class="connector-cell">{_escape_html(row.from_connector)}</td>')
        parts.append(f"<td>{_escape_html(row.from_pin)}</td>")
        parts.append(f'<td class="connector-cell">{_escape_html(row.to_connector)}</td>')
        parts.append(f"<td>{_escape_html(row.to_pin)}</td>")
        parts.append(f'<td class="cable-cell">{_escape_html(row.cable)}</td>')
        parts.append(f"<td>{row.core}</td>")
        parts.append(f"<td>{_escape_html(row.label)}</td>")
        parts.append(f'<td class="color-cell">{_escape_html(row.color)}</td>')
        parts.append(f"<td>{_escape_html(row.pair_group)}</td>")
        parts.append(f'<td class="notes-cell">{_escape_html(row.notes)}</td>')
        parts.append("</tr>")
    parts.append("</tbody>")

    parts.append("</table>")

    return "\n".join(parts)


def generate_wiring_table_svg_snippet(
    document: HarnessDocument,
    x: float = 0,
    y: float = 0,
    max_width: float = 280,
    row_height: float = 4,
    font_size: float = 2.5,
) -> str:
    """
    Generate wiring table as SVG elements for direct embedding.

    This creates SVG text and rect elements that can be inserted
    directly into an SVG document.

    Args:
        document: The HarnessDocument.
        x: X offset for the table.
        y: Y offset for the table.
        max_width: Maximum table width.
        row_height: Height of each row.
        font_size: Font size for text.

    Returns:
        SVG elements as a string.
    """
    rows = _build_wiring_table_rows(document)

    # Simplified columns for SVG (compact version)
    compact_headers = ["From", "Pin", "To", "Pin", "Cable", "Core", "Wire", "Color"]
    col_widths = [30, 15, 30, 15, 25, 15, 35, 20]  # mm widths

    parts = []
    parts.append(f'<g id="wiring-table" transform="translate({x}, {y})">')

    # Styles
    parts.append("""<style type="text/css">
    .wt-header { font-family: Arial; font-size: 2.5px; font-weight: bold; fill: white; }
    .wt-cell { font-family: Arial; font-size: 2.2px; fill: #333; }
    .wt-header-bg { fill: #4a4a4a; }
    .wt-row-even { fill: #f5f5f5; }
    .wt-row-odd { fill: white; }
    .wt-border { stroke: #ccc; stroke-width: 0.1; fill: none; }
    </style>""")

    total_width = sum(col_widths)

    # Header row
    current_x = 0
    parts.append(f'<rect x="0" y="0" width="{total_width}" height="{row_height}" class="wt-header-bg"/>')

    for i, (header, width) in enumerate(zip(compact_headers, col_widths)):
        text_x = current_x + 1
        text_y = row_height * 0.7
        parts.append(f'<text x="{text_x}" y="{text_y}" class="wt-header">{header}</text>')
        current_x += width

    # Data rows
    current_y = row_height
    for row_idx, row in enumerate(rows):
        # Row background
        bg_class = "wt-row-even" if row_idx % 2 == 0 else "wt-row-odd"
        parts.append(f'<rect x="0" y="{current_y}" width="{total_width}" height="{row_height}" class="{bg_class}"/>')

        # Cell values (compact)
        values = [
            row.from_connector,
            row.from_pin,
            row.to_connector,
            row.to_pin,
            row.cable,
            str(row.core),
            row.label[:10],  # Truncate
            row.color,
        ]

        current_x = 0
        for value, width in zip(values, col_widths):
            text_x = current_x + 1
            text_y = current_y + row_height * 0.7
            parts.append(f'<text x="{text_x}" y="{text_y}" class="wt-cell">{_escape_xml(value)}</text>')
            current_x += width

        current_y += row_height

    # Table border
    parts.append(f'<rect x="0" y="0" width="{total_width}" height="{current_y}" class="wt-border"/>')

    parts.append('</g>')

    return "\n".join(parts)


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
