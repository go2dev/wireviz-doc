"""
SVG composition module for WireViz Doc.

Combines WireViz diagram SVG output with templates to create complete
engineering drawings with title blocks, BOM tables, and wiring tables.

Uses lxml for reliable XML manipulation.

Usage:
    from wireviz_doc.composers.svg_composer import compose_svg

    final_svg = compose_svg(
        template_path="templates/sheet-a4.svg.j2",
        diagram_svg=wireviz_output,
        metadata=document.metadata,
        bom_data=bom_items,
    )
"""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from jinja2 import Environment, FileSystemLoader, select_autoescape

from wireviz_doc.generators.bom import get_bom_data
from wireviz_doc.models.document import DocumentMeta, HarnessDocument
from wireviz_doc.output import logger

# Try to import lxml for better XML handling, fall back to xml.etree
try:
    from lxml import etree as ET

    LXML_AVAILABLE = True
except ImportError:
    import xml.etree.ElementTree as ET

    LXML_AVAILABLE = False
    logger.warning("lxml not available, using xml.etree (limited functionality)")


# SVG namespace
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

# Namespace map for lxml
NSMAP = {
    None: SVG_NS,
    "xlink": XLINK_NS,
}


def _load_svg(svg_content: str) -> Any:
    """
    Load SVG content into an element tree.

    Args:
        svg_content: SVG content as string.

    Returns:
        Root element of the parsed SVG.
    """
    if LXML_AVAILABLE:
        parser = ET.XMLParser(remove_blank_text=True)
        return ET.fromstring(svg_content.encode("utf-8"), parser)
    else:
        return ET.fromstring(svg_content)


def _serialize_svg(root: Any) -> str:
    """
    Serialize SVG element tree to string.

    Args:
        root: Root element to serialize.

    Returns:
        SVG content as string.
    """
    if LXML_AVAILABLE:
        return ET.tostring(
            root,
            encoding="unicode",
            pretty_print=True,
            xml_declaration=True,
        )
    else:
        return ET.tostring(root, encoding="unicode")


def _find_element_by_id(root: Any, element_id: str) -> Optional[Any]:
    """
    Find an element by its id attribute.

    Args:
        root: Root element to search.
        element_id: ID to find.

    Returns:
        Element with matching id, or None.
    """
    if LXML_AVAILABLE:
        results = root.xpath(f'//*[@id="{element_id}"]')
        return results[0] if results else None
    else:
        # Standard library ElementTree
        for elem in root.iter():
            if elem.get("id") == element_id:
                return elem
        return None


def _replace_text_by_id(root: Any, element_id: str, new_text: str) -> bool:
    """
    Replace text content of an element by ID.

    Args:
        root: Root element.
        element_id: ID of element to update.
        new_text: New text content.

    Returns:
        True if element was found and updated.
    """
    elem = _find_element_by_id(root, element_id)
    if elem is not None:
        elem.text = new_text
        return True
    return False


def _insert_svg_into_element(
    parent: Any,
    svg_content: str,
    transform: Optional[str] = None,
) -> Any:
    """
    Insert SVG content into a parent element.

    Args:
        parent: Parent element to insert into.
        svg_content: SVG content to insert.
        transform: Optional transform attribute for positioning.

    Returns:
        The inserted group element.
    """
    # Parse the SVG to insert
    try:
        inserted_root = _load_svg(svg_content)
    except Exception as e:
        logger.error(f"Failed to parse SVG content: {e}")
        # Create placeholder
        if LXML_AVAILABLE:
            group = ET.SubElement(parent, "g")
            text = ET.SubElement(group, "text", x="10", y="20")
            text.text = "Failed to load diagram"
        else:
            group = ET.SubElement(parent, "g")
            text = ET.SubElement(group, "text")
            text.set("x", "10")
            text.set("y", "20")
            text.text = "Failed to load diagram"
        return group

    # Create a group to contain the inserted content
    if LXML_AVAILABLE:
        group = ET.SubElement(parent, "g", nsmap=NSMAP)
    else:
        group = ET.SubElement(parent, "g")

    if transform:
        group.set("transform", transform)

    # Copy all children from the inserted SVG
    for child in inserted_root:
        group.append(copy.deepcopy(child))

    return group


def _get_svg_dimensions(svg_content: str) -> tuple[float, float]:
    """
    Extract width and height from SVG content.

    Args:
        svg_content: SVG content.

    Returns:
        Tuple of (width, height) in user units.
    """
    try:
        root = _load_svg(svg_content)

        # Try viewBox first
        viewbox = root.get("viewBox")
        if viewbox:
            parts = viewbox.split()
            if len(parts) >= 4:
                return float(parts[2]), float(parts[3])

        # Try width/height attributes
        width = root.get("width", "0")
        height = root.get("height", "0")

        # Strip units
        width_val = float(re.sub(r"[^\d.]", "", width) or "0")
        height_val = float(re.sub(r"[^\d.]", "", height) or "0")

        return width_val, height_val
    except Exception:
        return 0.0, 0.0


def compose_svg_from_template(
    template_path: Union[str, Path],
    diagram_svg: str,
    metadata: DocumentMeta,
    bom_data: Optional[List[Dict[str, Any]]] = None,
    wiring_data: Optional[List[Dict[str, Any]]] = None,
    page_type: str = "diagram",
    notes: Optional[List[str]] = None,
    sheet_number: int = 1,
    total_sheets: int = 1,
) -> str:
    """
    Compose final SVG using a Jinja2 template.

    Args:
        template_path: Path to the SVG template (Jinja2).
        diagram_svg: WireViz diagram SVG content.
        metadata: Document metadata.
        bom_data: BOM data for the template.
        wiring_data: Wiring table data for the template.
        page_type: Type of page ("diagram", "bom", "wiring", "combined").
        notes: Optional list of notes.
        sheet_number: Current sheet number.
        total_sheets: Total number of sheets.

    Returns:
        Rendered SVG content.
    """
    template_path = Path(template_path)

    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(["html", "xml", "svg"]),
    )

    template = env.get_template(template_path.name)

    # Prepare metadata dict for template
    # All optional fields use `or ""` for consistent null handling
    meta_dict = {
        "id": metadata.id,
        "title": metadata.title,
        "revision": metadata.revision,
        "date": metadata.get_date_string() if hasattr(metadata, "get_date_string") else str(metadata.date),
        "author": metadata.author or "",
        "checker": getattr(metadata, "checker", None) or "",
        "approver": metadata.approver or "",
        "company": metadata.company or "",
        "department": getattr(metadata, "department", None) or "",
        "client": getattr(metadata, "client", None) or "",
        "project": metadata.project or "",
        "description": metadata.description or "",
        "sheet": sheet_number,
        "total_sheets": total_sheets,
        "scale": getattr(metadata, "scale", "NTS") or "NTS",
        "units": getattr(metadata, "units", "mm") or "mm",
    }

    # Add custom fields
    if metadata.custom_fields:
        meta_dict.update(metadata.custom_fields)

    # Render template
    rendered = template.render(
        metadata=meta_dict,
        diagram_svg=diagram_svg,
        bom=bom_data,
        wiring=wiring_data,
        page_type=page_type,
        notes=notes,
        show_bom=bom_data is not None and len(bom_data) > 0,
        show_wiring=wiring_data is not None,
    )

    logger.debug(f"Rendered SVG template: {template_path}")
    return rendered


def compose_svg_direct(
    template_svg: str,
    diagram_svg: str,
    metadata: DocumentMeta,
    bom_svg: Optional[str] = None,
    wiring_svg: Optional[str] = None,
) -> str:
    """
    Compose final SVG by directly manipulating SVG elements.

    This is an alternative to template rendering that works with
    pre-existing SVG templates containing placeholder elements.

    Args:
        template_svg: Base template SVG content.
        diagram_svg: WireViz diagram SVG to insert.
        metadata: Document metadata for title block.
        bom_svg: Optional BOM table SVG snippet.
        wiring_svg: Optional wiring table SVG snippet.

    Returns:
        Composed SVG content.
    """
    root = _load_svg(template_svg)

    # Find and populate diagram area
    diagram_area = _find_element_by_id(root, "diagram-area")
    if diagram_area is not None:
        # Clear existing content
        diagram_area.clear()
        diagram_area.set("id", "diagram-area")

        # Insert diagram
        _insert_svg_into_element(diagram_area, diagram_svg, "translate(2, 2)")

    # Find and populate BOM area
    if bom_svg:
        bom_area = _find_element_by_id(root, "bom-area")
        if bom_area is not None:
            _insert_svg_into_element(bom_area, bom_svg, "translate(2, 2)")

    # Find and populate wiring table area
    if wiring_svg:
        wiring_area = _find_element_by_id(root, "wiring-area")
        if wiring_area is not None:
            _insert_svg_into_element(wiring_area, wiring_svg, "translate(2, 2)")

    # Update title block text elements
    # All optional fields use `or ""` for consistent null handling
    title_block_fields = {
        "tb-title": metadata.title,
        "tb-doc-id": metadata.id,
        "tb-revision": metadata.revision,
        "tb-date": metadata.get_date_string() if hasattr(metadata, "get_date_string") else str(metadata.date),
        "tb-author": metadata.author or "",
        "tb-checker": getattr(metadata, "checker", None) or "",
        "tb-approver": metadata.approver or "",
        "tb-company": metadata.company or "",
        "tb-department": getattr(metadata, "department", None) or "",
        "tb-client": getattr(metadata, "client", None) or "",
        "tb-project": metadata.project or "",
        "tb-description": metadata.description or "",
        "tb-scale": getattr(metadata, "scale", "NTS") or "NTS",
        "tb-units": getattr(metadata, "units", "mm") or "mm",
    }

    for field_id, value in title_block_fields.items():
        if value:
            _replace_text_by_id(root, field_id, str(value))

    return _serialize_svg(root)


def compose_final_svg(
    document: HarnessDocument,
    diagram_svg_path: Union[str, Path],
    template_path: Union[str, Path],
    output_path: Union[str, Path],
    bom_data: Optional[List[Dict[str, Any]]] = None,
) -> Path:
    """
    Compose the final SVG document from all components.

    This is the main entry point for composing complete drawings.

    Args:
        document: The HarnessDocument.
        diagram_svg_path: Path to the WireViz-generated diagram SVG.
        template_path: Path to the SVG template.
        output_path: Path for the output SVG.
        bom_data: Optional BOM data (if None, extracted from document).

    Returns:
        Path to the generated SVG file.
    """
    diagram_svg_path = Path(diagram_svg_path)
    template_path = Path(template_path)
    output_path = Path(output_path)

    # Read diagram SVG
    diagram_svg = ""
    if diagram_svg_path.exists():
        with open(diagram_svg_path, "r", encoding="utf-8") as f:
            diagram_svg = f.read()
    else:
        logger.warning(f"Diagram SVG not found: {diagram_svg_path}")
        diagram_svg = """<svg><text x="10" y="20">Diagram not available</text></svg>"""

    # Get BOM data if not provided
    if bom_data is None:
        bom_data = get_bom_data(document)

    # Compose using template
    final_svg = compose_svg_from_template(
        template_path=template_path,
        diagram_svg=diagram_svg,
        metadata=document.metadata,
        bom_data=bom_data,
        page_type="diagram",
    )

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_svg)

    logger.info(f"Composed final SVG: {output_path}")
    return output_path


def get_template_path(template_name: str = "sheet-a4.svg.j2") -> Path:
    """
    Get the path to a built-in template.

    Args:
        template_name: Name of the template file.

    Returns:
        Path to the template.
    """
    # Templates are in the package templates directory
    templates_dir = Path(__file__).parent.parent / "templates"
    template_path = templates_dir / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    return template_path
