"""Metadata schema definitions for WireViz Document templates.

This module defines the canonical set of metadata fields available for use
in SVG templates. Template authors should reference this schema to know
which variables are available during template rendering.

Usage in Jinja2 templates:
    {{ metadata.id }}
    {{ metadata.title }}
    {{ metadata.custom_fields.my_field }}

Example YAML:
    metadata:
      id: "WH-001"
      title: "Main Power Harness"
      revision: "A"
      date: "2024-01-15"
      author: "J. Smith"
      custom_fields:
        length_tolerance: "+/- 5mm"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# =============================================================================
# METADATA FIELD DEFINITIONS
# =============================================================================

# Core required fields that must be present in every harness document
REQUIRED_METADATA_FIELDS = [
    "id",       # Unique document identifier (e.g., "WH-001", "IO-CABLE-20P")
    "title",    # Human-readable document title
    "revision", # Revision string (e.g., "A", "1.0", "Rev B")
    "date",     # Document date (ISO format: YYYY-MM-DD or datetime)
]

# Standard optional fields with defined semantics
STANDARD_METADATA_FIELDS = {
    # -------------------------------------------------------------------------
    # AUTHORSHIP & APPROVAL
    # -------------------------------------------------------------------------
    "author": {
        "description": "Name of the document author / drafter",
        "example": "J. Smith",
        "template_var": "metadata.author",
        "common_aliases": ["drawn_by", "drafter", "creator"],
    },
    "checker": {
        "description": "Name of the person who checked/reviewed the document",
        "example": "A. Jones",
        "template_var": "metadata.checker",
        "common_aliases": ["reviewed_by", "checked_by"],
    },
    "approver": {
        "description": "Name of the document approver",
        "example": "B. Williams",
        "template_var": "metadata.approver",
        "common_aliases": ["approved_by"],
    },

    # -------------------------------------------------------------------------
    # ORGANIZATION
    # -------------------------------------------------------------------------
    "company": {
        "description": "Company or organization name",
        "example": "Acme Electronics",
        "template_var": "metadata.company",
        "common_aliases": ["organization", "org"],
    },
    "department": {
        "description": "Department or team name",
        "example": "Engineering",
        "template_var": "metadata.department",
        "common_aliases": ["team", "division"],
    },
    "client": {
        "description": "Client or customer name (for contract work)",
        "example": "Customer Corp",
        "template_var": "metadata.client",
        "common_aliases": ["customer"],
    },

    # -------------------------------------------------------------------------
    # PROJECT INFORMATION
    # -------------------------------------------------------------------------
    "project": {
        "description": "Project name or number",
        "example": "Project Phoenix",
        "template_var": "metadata.project",
        "common_aliases": ["project_name", "project_number"],
    },
    "description": {
        "description": "Detailed description of the harness/document",
        "example": "Main power distribution harness for motor controller",
        "template_var": "metadata.description",
        "common_aliases": ["notes", "summary"],
    },

    # -------------------------------------------------------------------------
    # DRAWING SPECIFICS
    # -------------------------------------------------------------------------
    "scale": {
        "description": "Drawing scale (or 'NTS' for not to scale)",
        "example": "1:1",
        "template_var": "metadata.scale",
        "default": "NTS",
    },
    "units": {
        "description": "Primary units used in the document",
        "example": "mm",
        "template_var": "metadata.units",
        "default": "mm",
        "valid_values": ["mm", "cm", "in", "ft", "m"],
    },
    "sheet": {
        "description": "Current sheet number (for multi-sheet documents)",
        "example": 1,
        "template_var": "metadata.sheet",
        "default": 1,
    },
    "total_sheets": {
        "description": "Total number of sheets in document set",
        "example": 1,
        "template_var": "metadata.total_sheets",
        "default": 1,
    },

    # -------------------------------------------------------------------------
    # CUSTOM EXTENSION FIELDS
    # -------------------------------------------------------------------------
    "custom_fields": {
        "description": "Dictionary of user-defined custom fields",
        "example": {"length_tolerance": "+/- 5mm", "cable_type": "Shielded"},
        "template_var": "metadata.custom_fields.<field_name>",
        "notes": "Any key-value pairs can be added here for template use",
    },
}

# All template variables available during SVG rendering
TEMPLATE_VARIABLES = {
    # -------------------------------------------------------------------------
    # METADATA OBJECT
    # All fields from the metadata section of the YAML
    # -------------------------------------------------------------------------
    "metadata": {
        "description": "Document metadata object",
        "fields": {
            "id": "Document identifier",
            "title": "Document title",
            "revision": "Revision string",
            "date": "Document date (may be date object or string)",
            "author": "Author name",
            "checker": "Checker/reviewer name",
            "approver": "Approver name",
            "company": "Company name",
            "department": "Department name",
            "client": "Client name",
            "project": "Project name",
            "description": "Description text",
            "scale": "Drawing scale",
            "units": "Primary units",
            "sheet": "Current sheet number",
            "total_sheets": "Total sheets",
            "custom_fields": "Dict of custom key-value pairs",
        },
    },

    # -------------------------------------------------------------------------
    # BOM DATA (for bom-table.svg.j2)
    # -------------------------------------------------------------------------
    "bom_items": {
        "description": "List of BOM items",
        "fields": {
            "item_number": "Line item number",
            "quantity": "Quantity with unit",
            "reference": "Reference designators",
            "part_number": "Internal part number",
            "manufacturer": "Manufacturer name",
            "mpn": "Manufacturer part number",
            "description": "Part description",
            "alternates": "List of alternate parts",
        },
    },

    # -------------------------------------------------------------------------
    # WIRING TABLE DATA (for wiring-table.svg.j2)
    # -------------------------------------------------------------------------
    "wiring_rows": {
        "description": "List of wiring table rows",
        "fields": {
            "from_connector": "Source connector ID",
            "from_pin": "Source pin number",
            "to_connector": "Destination connector ID",
            "to_pin": "Destination pin number",
            "cable": "Cable ID",
            "core": "Core/wire number",
            "label": "Wire label",
            "color": "Wire color code",
            "pair_group": "Twisted pair group number",
            "notes": "Connection notes",
        },
    },

    # -------------------------------------------------------------------------
    # COMPONENT DATA
    # -------------------------------------------------------------------------
    "connectors": {
        "description": "Dictionary of connectors keyed by ID",
        "fields": {
            "pincount": "Number of pins",
            "type": "Connector type",
            "pinlabels": "List of pin labels",
            "notes": "Connector notes",
        },
    },
    "cables": {
        "description": "Dictionary of cables keyed by ID",
        "fields": {
            "wirecount": "Number of wires/cores",
            "gauge": "Wire gauge",
            "length": "Cable length",
            "colors": "List of wire colors",
            "wirelabels": "List of wire labels",
            "notes": "Cable notes",
        },
    },

    # -------------------------------------------------------------------------
    # POSITIONING VARIABLES (for component templates)
    # -------------------------------------------------------------------------
    "title_block_x": {
        "description": "X offset for title block positioning",
        "default": 0,
    },
    "title_block_y": {
        "description": "Y offset for title block positioning",
        "default": 0,
    },
}


@dataclass
class MetadataFieldSpec:
    """Specification for a metadata field."""

    name: str
    description: str
    required: bool = False
    default: Any = None
    example: Any = None
    valid_values: Optional[List[Any]] = None
    template_var: str = ""

    def __post_init__(self):
        if not self.template_var:
            self.template_var = f"metadata.{self.name}"


# Build the complete field specification list
def get_metadata_field_specs() -> List[MetadataFieldSpec]:
    """Get list of all metadata field specifications."""
    specs = []

    # Required fields
    for field_name in REQUIRED_METADATA_FIELDS:
        specs.append(MetadataFieldSpec(
            name=field_name,
            description=f"Required: {field_name}",
            required=True,
        ))

    # Standard optional fields
    for field_name, field_info in STANDARD_METADATA_FIELDS.items():
        specs.append(MetadataFieldSpec(
            name=field_name,
            description=field_info.get("description", ""),
            required=False,
            default=field_info.get("default"),
            example=field_info.get("example"),
            valid_values=field_info.get("valid_values"),
            template_var=field_info.get("template_var", f"metadata.{field_name}"),
        ))

    return specs


def get_template_variable_docs() -> str:
    """Generate documentation for all template variables."""
    lines = [
        "# Template Variable Reference",
        "",
        "This document lists all variables available in WireViz-Doc SVG templates.",
        "",
        "## Metadata Fields",
        "",
        "| Variable | Description | Required | Default |",
        "|----------|-------------|----------|---------|",
    ]

    for spec in get_metadata_field_specs():
        req = "Yes" if spec.required else "No"
        default = spec.default if spec.default is not None else "-"
        lines.append(f"| `{spec.template_var}` | {spec.description} | {req} | {default} |")

    lines.extend([
        "",
        "## Custom Fields",
        "",
        "Custom fields can be accessed via `metadata.custom_fields.<field_name>`.",
        "",
        "Example YAML:",
        "```yaml",
        "metadata:",
        "  custom_fields:",
        "    length_tolerance: '+/- 5mm'",
        "    cable_type: 'Shielded'",
        "```",
        "",
        "Example template usage:",
        "```jinja2",
        "{{ metadata.custom_fields.length_tolerance }}",
        "{{ metadata.custom_fields.cable_type }}",
        "```",
    ])

    return "\n".join(lines)


# Export schema for external tools
METADATA_SCHEMA = {
    "type": "object",
    "required": REQUIRED_METADATA_FIELDS,
    "properties": {
        "id": {"type": "string", "description": "Unique document identifier"},
        "title": {"type": "string", "description": "Document title"},
        "revision": {"type": "string", "description": "Revision string"},
        "date": {
            "oneOf": [
                {"type": "string", "format": "date"},
                {"type": "string"},
            ],
            "description": "Document date",
        },
        "author": {"type": "string", "description": "Author name"},
        "checker": {"type": "string", "description": "Checker/reviewer name"},
        "approver": {"type": "string", "description": "Approver name"},
        "company": {"type": "string", "description": "Company name"},
        "department": {"type": "string", "description": "Department name"},
        "client": {"type": "string", "description": "Client name"},
        "project": {"type": "string", "description": "Project name"},
        "description": {"type": "string", "description": "Document description"},
        "scale": {"type": "string", "default": "NTS", "description": "Drawing scale"},
        "units": {
            "type": "string",
            "enum": ["mm", "cm", "in", "ft", "m"],
            "default": "mm",
            "description": "Primary units",
        },
        "sheet": {"type": "integer", "default": 1, "description": "Sheet number"},
        "total_sheets": {"type": "integer", "default": 1, "description": "Total sheets"},
        "custom_fields": {
            "type": "object",
            "additionalProperties": True,
            "description": "User-defined custom fields",
        },
    },
}
