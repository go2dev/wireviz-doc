"""
YAML parsing module for WireViz Doc.

This module parses unified WireViz-compatible YAML files that contain both
standard WireViz sections (connectors, cables, connections) and extended
metadata sections (metadata, parts, accessories, connection_info).

The same YAML file can be:
- Processed directly by WireViz for diagram generation
- Processed by wvdoc for full documentation (BOM, wiring tables, title blocks)

Usage:
    from wireviz_doc.parser import parse_harness_yaml

    document = parse_harness_yaml("harness.yml")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import ValidationError

from wireviz_doc.models.base import ColorSpec, ImageSpec, Quantity
from wireviz_doc.models.components import Cable, Connector, Core
from wireviz_doc.models.connections import Connection
from wireviz_doc.models.document import DocumentMeta, HarnessDocument
from wireviz_doc.models.parts import Accessory, AccessoryType, AlternatePart, Part
from wireviz_doc.output import logger


class ParserError(Exception):
    """Exception raised when parsing fails."""

    def __init__(self, message: str, path: Optional[Path] = None, details: Optional[List[str]] = None):
        self.message = message
        self.path = path
        self.details = details or []
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format the error message with details."""
        msg = self.message
        if self.path:
            msg = f"{self.path}: {msg}"
        if self.details:
            msg += "\n" + "\n".join(f"  - {d}" for d in self.details)
        return msg


def load_yaml_file(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML file with full anchor/reference support.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        ParserError: If the file cannot be read or parsed.
    """
    path = Path(path)

    if not path.exists():
        raise ParserError("File not found", path=path)

    if not path.is_file():
        raise ParserError("Not a file", path=path)

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = yaml.load(f, Loader=yaml.FullLoader)
    except yaml.YAMLError as e:
        raise ParserError(f"Invalid YAML syntax: {e}", path=path)
    except IOError as e:
        raise ParserError(f"Cannot read file: {e}", path=path)

    if content is None:
        raise ParserError("Empty YAML file", path=path)

    if not isinstance(content, dict):
        raise ParserError("YAML root must be a mapping/dictionary", path=path)

    return content


def _parse_alternates(alternates_data: List[Dict[str, Any]]) -> List[AlternatePart]:
    """Parse alternate parts list."""
    result = []
    for alt in alternates_data:
        result.append(AlternatePart(
            manufacturer=alt.get("manufacturer", ""),
            mpn=alt.get("mpn", ""),
            vendor_sku=alt.get("spn") or alt.get("vendor_sku"),
            url=alt.get("url"),
        ))
    return result


def _parse_image(image_data: Optional[Union[str, Dict[str, Any]]]) -> Optional[ImageSpec]:
    """Parse image specification."""
    if image_data is None:
        return None

    if isinstance(image_data, str):
        return ImageSpec(src=image_data)

    if isinstance(image_data, dict):
        return ImageSpec(
            src=image_data.get("src", ""),
            caption=image_data.get("caption"),
            height=str(image_data.get("height")) if image_data.get("height") else None,
        )

    return None


def _parse_quantity(qty_data: Union[str, int, float, Dict[str, Any]]) -> Quantity:
    """Parse a quantity specification."""
    if isinstance(qty_data, (int, float)):
        return Quantity(value=float(qty_data), unit="pcs")

    if isinstance(qty_data, str):
        qty_str = qty_data.strip()
        i = 0
        while i < len(qty_str) and (qty_str[i].isdigit() or qty_str[i] == '.'):
            i += 1

        if i == 0:
            return Quantity(value=1.0, unit=qty_str)

        value = float(qty_str[:i])
        unit = qty_str[i:].strip() or "pcs"
        return Quantity(value=value, unit=unit)

    if isinstance(qty_data, dict):
        return Quantity(
            value=float(qty_data.get("value", 0)),
            unit=qty_data.get("unit", "pcs"),
        )

    return Quantity(value=1.0, unit="pcs")


def _parse_parts(parts_data: Dict[str, Any]) -> Dict[str, Part]:
    """Parse the parts library section (WireViz ignores this)."""
    result = {}

    for part_id, part_info in parts_data.items():
        if not isinstance(part_info, dict):
            continue

        alternates = _parse_alternates(part_info.get("alternates", []))
        image = _parse_image(part_info.get("image"))

        result[part_id] = Part(
            id=part_id,
            primary_pn=part_info.get("primary_pn", part_info.get("pn", part_id)),
            manufacturer=part_info.get("manufacturer", ""),
            mpn=part_info.get("mpn", ""),
            description=part_info.get("description", ""),
            alternates=alternates,
            fields=part_info.get("fields", {}),
            image=image,
        )

    return result


def _parse_color(color_data: Union[str, Dict[str, Any]]) -> ColorSpec:
    """Parse a color specification."""
    if isinstance(color_data, str):
        return ColorSpec.parse(color_data)
    if isinstance(color_data, dict):
        return ColorSpec(
            display_color=color_data.get("display_color", ""),
            base_color=color_data.get("base_color", ""),
            stripe_color=color_data.get("stripe_color"),
        )
    raise ValueError(f"Invalid color specification: {color_data}")


def _parse_cores_from_wireviz(
    colors: List[str],
    wirelabels: Optional[List[str]] = None,
) -> List[Core]:
    """
    Parse cores from WireViz-native colors and wirelabels arrays.

    Args:
        colors: List of color codes (e.g., ["RD", "BK", "BU-WH"])
        wirelabels: Optional list of wire labels

    Returns:
        List of Core objects
    """
    result = []
    wirelabels = wirelabels or []

    for i, color_str in enumerate(colors):
        color = _parse_color(color_str)
        label = wirelabels[i] if i < len(wirelabels) else None

        # Try to detect pair groups from color patterns (solid + stripe)
        pair_group = None
        if i % 2 == 0 and i + 1 < len(colors):
            # Check if this and next form a pair (same base, one has stripe)
            pair_group = (i // 2) + 1

        result.append(Core(
            index=i,  # 0-based internally
            color=color,
            label=label,
            pair_group=pair_group,
        ))

    return result


def _parse_connectors(
    connectors_data: Dict[str, Any],
    parts: Dict[str, Part],
) -> Dict[str, Connector]:
    """
    Parse connectors section (WireViz-native format with extended part lookup).

    Connectors can reference parts via `pn` field for BOM generation.
    """
    result = {}

    for conn_id, conn_info in connectors_data.items():
        if not isinstance(conn_info, dict):
            continue

        # Get part reference - can be via `pn` or `part` field
        part_ref = conn_info.get("pn") or conn_info.get("part")
        part = parts.get(part_ref) if part_ref else None

        # Build connector - prefer WireViz-native fields, fallback to part library
        if part:
            primary_pn = conn_info.get("pn", part.primary_pn)
            manufacturer = conn_info.get("manufacturer", part.manufacturer)
            mpn = conn_info.get("mpn", part.mpn)
            description = part.description
            alternates = part.alternates
            image = _parse_image(conn_info.get("image")) or part.image
            fields = {**part.fields, **conn_info.get("fields", {})}
        else:
            primary_pn = conn_info.get("pn", f"PN-{conn_id}")
            manufacturer = conn_info.get("manufacturer", "Unknown")
            mpn = conn_info.get("mpn", "")
            description = conn_info.get("description", f"Connector {conn_id}")
            alternates = _parse_alternates(conn_info.get("alternates", []))
            image = _parse_image(conn_info.get("image"))
            fields = conn_info.get("fields", {})

        # Determine connector type
        type_str = conn_info.get("type", "other")
        subtype_str = conn_info.get("subtype", "")
        from wireviz_doc.models.components import ConnectorType
        try:
            conn_type = ConnectorType(type_str.lower())
        except ValueError:
            conn_type = ConnectorType.OTHER

        pinlabels = conn_info.get("pinlabels", [])
        pincount = conn_info.get("pincount", len(pinlabels) if pinlabels else 1)

        result[conn_id] = Connector(
            id=conn_id,
            primary_pn=primary_pn,
            manufacturer=manufacturer,
            mpn=mpn,
            description=description,
            type=conn_type,
            subtype=subtype_str or type_str,
            pincount=pincount,
            pinlabels=pinlabels,
            alternates=alternates,
            fields=fields,
            image=image,
            notes=conn_info.get("notes"),
        )

    return result


def _parse_cables(
    cables_data: Dict[str, Any],
    parts: Dict[str, Part],
) -> Dict[str, Cable]:
    """
    Parse cables section (WireViz-native format with extended part lookup).

    Uses WireViz-native `colors` and `wirelabels` arrays.
    """
    result = {}

    for cable_id, cable_info in cables_data.items():
        if not isinstance(cable_info, dict):
            continue

        # Get part reference
        part_ref = cable_info.get("pn") or cable_info.get("part")
        part = parts.get(part_ref) if part_ref else None

        if part:
            primary_pn = cable_info.get("pn", part.primary_pn)
            manufacturer = cable_info.get("manufacturer", part.manufacturer)
            mpn = cable_info.get("mpn", part.mpn)
            description = part.description
            alternates = part.alternates
            image = _parse_image(cable_info.get("image")) or part.image
            fields = {**part.fields, **cable_info.get("fields", {})}
        else:
            primary_pn = cable_info.get("pn", f"PN-{cable_id}")
            manufacturer = cable_info.get("manufacturer", "Unknown")
            mpn = cable_info.get("mpn", "")
            description = cable_info.get("description", f"Cable {cable_id}")
            alternates = _parse_alternates(cable_info.get("alternates", []))
            image = _parse_image(cable_info.get("image"))
            fields = cable_info.get("fields", {})

        # Parse cores from WireViz-native colors/wirelabels
        colors = cable_info.get("colors", [])
        wirelabels = cable_info.get("wirelabels", [])
        cores = _parse_cores_from_wireviz(colors, wirelabels)

        wirecount = cable_info.get("wirecount", len(cores) if cores else 1)

        # Parse length
        length_data = cable_info.get("length", {"value": 0, "unit": "mm"})
        length = _parse_quantity(length_data)

        # Gauge
        gauge = cable_info.get("gauge", fields.get("gauge_awg", "22 AWG"))
        if isinstance(gauge, int):
            gauge = f"{gauge} AWG"

        # Parse shield - WireViz uses `shield: false` as boolean, we need None or ShieldSpec
        shield_data = cable_info.get("shield")
        shield = None
        if shield_data and not isinstance(shield_data, bool):
            # Parse as ShieldSpec if it's a dict
            from wireviz_doc.models.components import ShieldSpec, ShieldType
            if isinstance(shield_data, dict):
                shield_type_str = shield_data.get("type", "braided")
                try:
                    shield_type = ShieldType(shield_type_str.lower())
                except ValueError:
                    shield_type = ShieldType.BRAIDED
                shield = ShieldSpec(
                    type=shield_type,
                    coverage=shield_data.get("coverage"),
                    drain_wire=shield_data.get("drain_wire", False),
                )

        result[cable_id] = Cable(
            id=cable_id,
            primary_pn=primary_pn,
            manufacturer=manufacturer,
            mpn=mpn,
            description=description,
            wirecount=wirecount,
            cores=cores,
            gauge=str(gauge),
            length=length,
            alternates=alternates,
            fields=fields,
            image=image,
            notes=cable_info.get("notes"),
            shield=shield,
        )

    return result


def _parse_connection_info(connection_info_data: List[Dict[str, Any]]) -> List[Connection]:
    """
    Parse extended connection_info section (WireViz ignores this).

    This section provides detailed per-wire info for wiring table generation.
    """
    result = []

    for conn in connection_info_data:
        if not isinstance(conn, dict):
            continue

        # Core is 1-based in YAML, convert to 0-based internally
        core = conn.get("core", 1)
        if core > 0:
            core = core - 1

        result.append(Connection(
            from_connector=str(conn.get("from", "")),
            from_pin=conn.get("pin", 1),
            cable=str(conn.get("cable", "")),
            core=core,
            to_connector=str(conn.get("to", "")),
            to_pin=conn.get("pin", 1),  # Same pin for straight-through
            notes=conn.get("notes"),
            signal_name=conn.get("label"),
            wire_label=conn.get("label"),
            pair_group=conn.get("pair"),
        ))

    return result


def _derive_connections_from_wireviz(
    connections_data: List[Any],
    cables: Dict[str, Cable],
) -> List[Connection]:
    """
    Derive Connection objects from WireViz-native connections format.

    WireViz format: [[{J1: [1,2,3]}, {W1: [1,2,3]}, {J2: [1,2,3]}], ...]
    """
    result = []

    for conn_group in connections_data:
        if not isinstance(conn_group, list) or len(conn_group) < 2:
            continue

        # Extract connector/cable/pin info from each element
        elements = []
        for elem in conn_group:
            if isinstance(elem, dict):
                for key, pins in elem.items():
                    elements.append((key, pins if isinstance(pins, list) else [pins]))

        if len(elements) < 2:
            continue

        # Find from_connector, cable, to_connector
        from_conn, from_pins = elements[0]
        cable_id, cores = None, []
        to_conn, to_pins = None, []

        for key, pins in elements[1:]:
            if key in cables:
                cable_id = key
                cores = pins
            else:
                to_conn = key
                to_pins = pins

        if not cable_id or not to_conn:
            continue

        cable = cables.get(cable_id)

        # Create connections for each wire
        for i, (from_pin, core, to_pin) in enumerate(zip(from_pins, cores, to_pins)):
            # Get label from cable cores if available
            label = None
            pair_group = None
            if cable and cable.cores:
                core_idx = core - 1  # cores in YAML are 1-based
                if 0 <= core_idx < len(cable.cores):
                    label = cable.cores[core_idx].label
                    pair_group = cable.cores[core_idx].pair_group

            result.append(Connection(
                from_connector=from_conn,
                from_pin=from_pin,
                cable=cable_id,
                core=core - 1,  # Convert to 0-based
                to_connector=to_conn,
                to_pin=to_pin,
                wire_label=label,
                pair_group=pair_group,
            ))

    return result


def _parse_accessories(
    accessories_data: Union[Dict[str, Any], List[Any]],
    parts: Dict[str, Part],
) -> List[Accessory]:
    """Parse accessories section (WireViz ignores this)."""
    result = []

    # Handle both dict and list formats
    if isinstance(accessories_data, dict):
        items = [{"id": k, **v} for k, v in accessories_data.items()]
    else:
        items = accessories_data

    for acc_info in items:
        if not isinstance(acc_info, dict):
            continue

        # Get accessory type
        type_str = acc_info.get("type", "other").lower()
        try:
            acc_type = AccessoryType(type_str)
        except ValueError:
            acc_type = AccessoryType.OTHER

        # Get part reference
        part_ref = acc_info.get("part")
        if isinstance(part_ref, str) and part_ref in parts:
            part = parts[part_ref]
        elif isinstance(part_ref, dict):
            part = Part(
                id=part_ref.get("id", f"ACC-{len(result)}"),
                primary_pn=part_ref.get("pn", part_ref.get("primary_pn", "")),
                manufacturer=part_ref.get("manufacturer", "Unknown"),
                mpn=part_ref.get("mpn", ""),
                description=part_ref.get("description", ""),
            )
        else:
            # Create minimal part from accessory info
            part = Part(
                id=acc_info.get("id", f"ACC-{len(result)}"),
                primary_pn=part_ref or "",
                manufacturer="",
                mpn="",
                description=acc_info.get("description", ""),
            )

        # Parse quantity
        qty = _parse_quantity(acc_info.get("qty", acc_info.get("quantity", 1)))
        if "qty_unit" in acc_info:
            qty = Quantity(value=qty.value, unit=acc_info["qty_unit"])

        result.append(Accessory(
            type=acc_type,
            part=part,
            quantity=qty,
            location=acc_info.get("location"),
            notes=acc_info.get("notes"),
        ))

    return result


def _parse_metadata(metadata_data: Dict[str, Any]) -> DocumentMeta:
    """Parse document metadata section (WireViz ignores this)."""
    return DocumentMeta(
        id=metadata_data.get("id", "UNKNOWN"),
        title=metadata_data.get("title", "Untitled Harness"),
        revision=metadata_data.get("revision", "A"),
        date=metadata_data.get("date", ""),
        author=metadata_data.get("author"),
        checker=metadata_data.get("checker"),
        approver=metadata_data.get("approver"),
        company=metadata_data.get("company"),
        department=metadata_data.get("department"),
        client=metadata_data.get("client"),
        project=metadata_data.get("project"),
        description=metadata_data.get("description"),
        scale=metadata_data.get("scale", "NTS"),
        units=metadata_data.get("units", "mm"),
        sheet=metadata_data.get("sheet", 1),
        total_sheets=metadata_data.get("total_sheets", 1),
        custom_fields=metadata_data.get("custom_fields", {}),
    )


def parse_harness_yaml(
    path: Union[str, Path],
    strict: bool = True,
) -> HarnessDocument:
    """
    Parse a unified WireViz-compatible YAML file into a HarnessDocument.

    The YAML file should contain:
    - Standard WireViz sections: connectors, cables, connections
    - Extended sections (ignored by WireViz): metadata, parts, accessories, connection_info

    Args:
        path: Path to the YAML file.
        strict: If True, raise on validation errors.

    Returns:
        A validated HarnessDocument model.

    Raises:
        ParserError: If the file cannot be parsed or fails validation.

    Example:
        >>> doc = parse_harness_yaml("my-harness.yml")
        >>> print(doc.metadata.title)
        "20-Pin IO Cable"
    """
    path = Path(path)
    logger.info(f"Parsing harness YAML: {path}")

    raw_data = load_yaml_file(path)

    try:
        # Parse metadata (required for wvdoc)
        if "metadata" not in raw_data:
            raise ParserError("Missing required 'metadata' section", path=path)
        metadata = _parse_metadata(raw_data["metadata"])
        logger.debug(f"Parsed metadata: {metadata.id} - {metadata.title}")

        # Parse parts library (extended section)
        parts = _parse_parts(raw_data.get("parts", {}))
        logger.debug(f"Parsed {len(parts)} parts")

        # Parse connectors (WireViz section)
        connectors = _parse_connectors(raw_data.get("connectors", {}), parts)
        logger.debug(f"Parsed {len(connectors)} connectors")

        # Parse cables (WireViz section)
        cables = _parse_cables(raw_data.get("cables", {}), parts)
        logger.debug(f"Parsed {len(cables)} cables")

        # Parse connections - prefer connection_info, fallback to deriving from WireViz connections
        if "connection_info" in raw_data:
            connections = _parse_connection_info(raw_data["connection_info"])
            logger.debug(f"Parsed {len(connections)} connections from connection_info")
        elif "connections" in raw_data:
            connections = _derive_connections_from_wireviz(raw_data["connections"], cables)
            logger.debug(f"Derived {len(connections)} connections from WireViz format")
        else:
            connections = []

        # Parse accessories (extended section)
        accessories = _parse_accessories(raw_data.get("accessories", []), parts)
        logger.debug(f"Parsed {len(accessories)} accessories")

        # Build document
        document = HarnessDocument(
            metadata=metadata,
            parts=parts,
            connectors=connectors,
            cables=cables,
            connections=connections,
            accessories=accessories,
            notes=raw_data.get("notes"),
        )

        logger.info(f"Successfully parsed harness document: {metadata.id}")
        return document

    except ValidationError as e:
        errors = [str(err) for err in e.errors()]
        raise ParserError("Validation failed", path=path, details=errors)
    except Exception as e:
        if isinstance(e, ParserError):
            raise
        raise ParserError(f"Unexpected error: {e}", path=path)


def validate_harness_yaml(path: Union[str, Path]) -> List[str]:
    """
    Validate a harness YAML file without fully parsing it.

    Returns a list of validation issues (empty if valid).
    """
    issues = []

    try:
        doc = parse_harness_yaml(path, strict=True)
        validation_issues = doc.validate_complete()
        issues.extend(validation_issues)
    except ParserError as e:
        issues.append(e.format_message())
        issues.extend(e.details)

    return issues
