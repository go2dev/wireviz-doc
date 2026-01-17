"""
WireViz YAML generation module.

Converts HarnessDocument models to pure WireViz-compatible YAML format.
Only includes keys that WireViz understands (connectors, cables, connections).

Usage:
    from wireviz_doc.generators.wireviz_yaml import generate_wireviz_yaml

    yaml_content = generate_wireviz_yaml(document)
    # or
    generate_wireviz_yaml_file(document, output_path, image_paths)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from wireviz_doc.models.document import HarnessDocument
from wireviz_doc.output import logger


def _build_connector_entry(
    connector_id: str,
    connector: Any,
    image_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a WireViz-compatible connector entry.

    WireViz connector keys:
    - type: str (optional, for display)
    - subtype: str (optional)
    - pincount: int
    - pinlabels: list[str]
    - image: dict with src and optional caption
    - notes: str
    """
    entry: Dict[str, Any] = {}

    # Type/subtype for display
    if connector.subtype:
        entry["type"] = connector.subtype
    elif connector.type:
        entry["type"] = str(connector.type.value)

    # Pin configuration
    entry["pincount"] = connector.pincount

    if connector.pinlabels:
        entry["pinlabels"] = connector.pinlabels

    # Image
    if image_path:
        entry["image"] = {"src": image_path}
        if connector.image and connector.image.caption:
            entry["image"]["caption"] = connector.image.caption
    elif connector.image:
        entry["image"] = {"src": connector.image.src}
        if connector.image.caption:
            entry["image"]["caption"] = connector.image.caption

    # Notes
    if connector.notes:
        entry["notes"] = connector.notes

    return entry


def _build_cable_entry(
    cable_id: str,
    cable: Any,
    image_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a WireViz-compatible cable entry.

    WireViz cable keys:
    - wirecount: int
    - gauge: str
    - length: str or number
    - color_code: str (optional)
    - colors: list[str] (optional)
    - wirelabels: list[str] (optional)
    - shield: bool or str (optional)
    - image: dict (optional)
    - notes: str (optional)
    """
    entry: Dict[str, Any] = {}

    # Wire configuration
    entry["wirecount"] = cable.wirecount
    entry["gauge"] = cable.gauge

    # Length - WireViz accepts number or string
    if cable.length:
        entry["length"] = str(cable.length)

    # Colors from cores
    if cable.cores:
        colors = []
        wirelabels = []
        for core in sorted(cable.cores, key=lambda c: c.index):
            colors.append(core.color.display_color)
            if core.label:
                wirelabels.append(core.label)
            else:
                wirelabels.append("")

        if colors:
            entry["colors"] = colors
        if any(wirelabels):
            entry["wirelabels"] = wirelabels

    # Shield
    if cable.shield:
        entry["shield"] = True

    # Image
    if image_path:
        entry["image"] = {"src": image_path}
    elif cable.image:
        entry["image"] = {"src": cable.image.src}

    # Notes
    if cable.notes:
        entry["notes"] = cable.notes

    return entry


def _build_connections(document: HarnessDocument) -> List[List[Any]]:
    """
    Build WireViz-compatible connection entries.

    WireViz connection format:
    - Each connection is a list: [{connector: [pins]}, {cable: [cores]}, {connector: [pins]}]
    - Connector format: {ID: [PIN1, PIN2, ...]} or just ID for all pins
    - Cable format: {ID: [CORE1, CORE2, ...]} or just ID for all cores

    For efficiency, we group connections by cable and attempt to batch them.
    """
    # Group connections by (from_connector, cable, to_connector)
    # to batch pins/cores that go together
    connection_groups: Dict[tuple, List[tuple]] = {}

    for conn in document.connections:
        key = (conn.from_connector, conn.cable, conn.to_connector)
        if key not in connection_groups:
            connection_groups[key] = []
        # Store (from_pin, core, to_pin) - convert core to 1-based
        connection_groups[key].append((conn.from_pin, conn.core + 1, conn.to_pin))

    result = []

    for (from_conn, cable_id, to_conn), pins_cores in connection_groups.items():
        # Sort by from_pin for consistent output
        pins_cores.sort(key=lambda x: (x[0] if isinstance(x[0], int) else 0))

        from_pins = [p[0] for p in pins_cores]
        cores = [p[1] for p in pins_cores]
        to_pins = [p[2] for p in pins_cores]

        connection = [
            {from_conn: from_pins},
            {cable_id: cores},
            {to_conn: to_pins},
        ]
        result.append(connection)

    return result


def generate_wireviz_yaml(
    document: HarnessDocument,
    image_paths: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate WireViz-compatible YAML content from a HarnessDocument.

    Args:
        document: The parsed HarnessDocument.
        image_paths: Optional dict mapping component IDs to resolved image paths.

    Returns:
        YAML string that can be processed by WireViz.

    Example:
        >>> yaml_content = generate_wireviz_yaml(document)
        >>> with open("wireviz.yml", "w") as f:
        ...     f.write(yaml_content)
    """
    image_paths = image_paths or {}

    wireviz_data: Dict[str, Any] = {}

    # Build connectors section
    connectors: Dict[str, Any] = {}
    for conn_id, connector in document.connectors.items():
        connectors[conn_id] = _build_connector_entry(
            conn_id,
            connector,
            image_paths.get(conn_id),
        )
    if connectors:
        wireviz_data["connectors"] = connectors

    # Build cables section
    cables: Dict[str, Any] = {}
    for cable_id, cable in document.cables.items():
        cables[cable_id] = _build_cable_entry(
            cable_id,
            cable,
            image_paths.get(cable_id),
        )
    if cables:
        wireviz_data["cables"] = cables

    # Build connections section
    connections = _build_connections(document)
    if connections:
        wireviz_data["connections"] = connections

    # Generate YAML with nice formatting
    yaml_content = yaml.dump(
        wireviz_data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )

    return yaml_content


def generate_wireviz_yaml_file(
    document: HarnessDocument,
    output_path: Union[str, Path],
    image_paths: Optional[Dict[str, str]] = None,
) -> Path:
    """
    Generate WireViz YAML file from a HarnessDocument.

    Args:
        document: The parsed HarnessDocument.
        output_path: Path for the output YAML file.
        image_paths: Optional dict mapping component IDs to resolved image paths.

    Returns:
        Path to the generated file.

    Example:
        >>> output = generate_wireviz_yaml_file(document, "build/harness/wireviz.yml")
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    yaml_content = generate_wireviz_yaml(document, image_paths)

    logger.info(f"Writing WireViz YAML to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    logger.debug(f"Generated WireViz YAML with {len(document.connectors)} connectors, "
                 f"{len(document.cables)} cables, {len(document.connections)} connections")

    return output_path
