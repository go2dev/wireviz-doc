"""Document-level models for WireViz document pipeline.

This module defines Pydantic models for the top-level harness document
structure, including document metadata and the complete harness specification
that aggregates all components, connections, and accessories.
"""

# NOTE: Not using `from __future__ import annotations` here due to
# Pydantic compatibility issues with datetime types in Python 3.14+

import datetime as dt
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from wireviz_doc.models.components import Cable, Connector
from wireviz_doc.models.connections import Connection, ConnectionGroup, SpliceConnection
from wireviz_doc.models.parts import Accessory, Part


class DocumentMeta(BaseModel):
    """Metadata for a harness document.

    Contains administrative and identification information about the
    harness documentation including revision control, authorship,
    and project association.

    See schema.py for the complete list of available fields and their
    usage in SVG templates.

    Attributes:
        id: Unique document identifier (e.g., document number).
        title: Human-readable document title.
        revision: Document revision string (e.g., "A", "1.0", "Rev B").
        date: Document date (creation or last revision).
        author: Name of the document author/drafter.
        checker: Name of the person who checked/reviewed the document.
        approver: Name of the document approver.
        company: Company or organization name.
        department: Department or team name.
        client: Client or customer name.
        project: Project name or number.
        description: Detailed document description.
        scale: Drawing scale (default: "NTS" for not to scale).
        units: Primary units (default: "mm").
        sheet: Current sheet number (default: 1).
        total_sheets: Total number of sheets (default: 1).
        custom_fields: Additional metadata as key-value pairs.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
        extra="allow",  # Allow additional fields for forward compatibility
    )

    # -------------------------------------------------------------------------
    # REQUIRED FIELDS
    # -------------------------------------------------------------------------
    id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Human-readable document title")
    revision: str = Field(..., description="Document revision string")
    date: Union[dt.date, dt.datetime, str] = Field(
        ..., description="Document date (creation or last revision)"
    )

    # -------------------------------------------------------------------------
    # AUTHORSHIP & APPROVAL (optional)
    # -------------------------------------------------------------------------
    author: Optional[str] = Field(
        default=None, description="Document author/drafter name"
    )
    checker: Optional[str] = Field(
        default=None, description="Document checker/reviewer name"
    )
    approver: Optional[str] = Field(
        default=None, description="Document approver name"
    )

    # -------------------------------------------------------------------------
    # ORGANIZATION (optional)
    # -------------------------------------------------------------------------
    company: Optional[str] = Field(default=None, description="Company name")
    department: Optional[str] = Field(
        default=None, description="Department or team name"
    )
    client: Optional[str] = Field(
        default=None, description="Client or customer name"
    )

    # -------------------------------------------------------------------------
    # PROJECT INFORMATION (optional)
    # -------------------------------------------------------------------------
    project: Optional[str] = Field(
        default=None, description="Project name or number"
    )
    description: Optional[str] = Field(
        default=None, description="Detailed document description"
    )

    # -------------------------------------------------------------------------
    # DRAWING SPECIFICS (optional with defaults)
    # -------------------------------------------------------------------------
    scale: str = Field(default="NTS", description="Drawing scale")
    units: str = Field(default="mm", description="Primary units")
    sheet: int = Field(default=1, description="Current sheet number")
    total_sheets: int = Field(default=1, description="Total number of sheets")

    # -------------------------------------------------------------------------
    # CUSTOM EXTENSION FIELDS
    # -------------------------------------------------------------------------
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata key-value pairs"
    )

    @field_validator("id", "title", "revision")
    @classmethod
    def validate_required_strings(cls, v: str, info: Any) -> str:
        """Ensure required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v: Union[dt.date, dt.datetime, str]) -> Union[dt.date, dt.datetime, str]:
        """Parse date from various formats."""
        if isinstance(v, (dt.date, dt.datetime)):
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Date cannot be empty")
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"]:
                try:
                    return dt.datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            # If no format matches, return as string for flexibility
            return v
        raise ValueError(f"Invalid date value: {v!r}")

    @field_validator(
        "author", "checker", "approver", "company", "department",
        "client", "project", "description", mode="before"
    )
    @classmethod
    def strip_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace from optional string fields."""
        if v is None:
            return None
        v = str(v).strip()
        return v if v else None

    def get_date_string(self, fmt: str = "%Y-%m-%d") -> str:
        """Get the date as a formatted string.

        Args:
            fmt: The date format string (strftime format).

        Returns:
            The formatted date string.
        """
        if isinstance(self.date, (dt.date, dt.datetime)):
            return self.date.strftime(fmt)
        return str(self.date)


class HarnessDocument(BaseModel):
    """Complete harness document specification.

    This is the top-level model representing an entire wire harness
    documentation package. It aggregates all components (connectors,
    cables), connections, parts, and accessories into a single
    cohesive document structure.

    Attributes:
        metadata: Document metadata (title, revision, author, etc.).
        parts: Dictionary of generic parts by ID.
        connectors: Dictionary of connectors by ID.
        cables: Dictionary of cables by ID.
        connections: List of all wire connections.
        accessories: List of harness-level accessories.
        connection_groups: Optional grouped connections for organization.
        splices: Optional list of splice connections.
        notes: Optional document-level notes.
        bom_extra: Optional additional BOM line items.

    Example:
        >>> doc = HarnessDocument(
        ...     metadata=DocumentMeta(
        ...         id="WH-001",
        ...         title="Main Power Harness",
        ...         revision="A",
        ...         date="2024-01-15",
        ...         author="J. Engineer"
        ...     ),
        ...     connectors={"J1": connector1, "J2": connector2},
        ...     cables={"W1": cable1},
        ...     connections=[conn1, conn2, conn3]
        ... )
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    metadata: DocumentMeta = Field(..., description="Document metadata")
    parts: Dict[str, Part] = Field(
        default_factory=dict, description="Generic parts by ID"
    )
    connectors: Dict[str, Connector] = Field(
        default_factory=dict, description="Connectors by ID"
    )
    cables: Dict[str, Cable] = Field(
        default_factory=dict, description="Cables by ID"
    )
    connections: List[Connection] = Field(
        default_factory=list, description="Wire connections"
    )
    accessories: List[Accessory] = Field(
        default_factory=list, description="Harness-level accessories"
    )
    connection_groups: Optional[List[ConnectionGroup]] = Field(
        default=None, description="Grouped connections for organization"
    )
    splices: Optional[List[SpliceConnection]] = Field(
        default=None, description="Splice connections"
    )
    notes: Optional[str] = Field(
        default=None, description="Document-level notes"
    )
    bom_extra: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Additional BOM line items"
    )

    @model_validator(mode="after")
    def validate_connection_references(self) -> HarnessDocument:
        """Validate that all connections reference valid connectors and cables."""
        errors: List[str] = []

        for i, conn in enumerate(self.connections):
            if conn.from_connector not in self.connectors:
                errors.append(
                    f"Connection {i}: from_connector '{conn.from_connector}' not found"
                )
            if conn.to_connector not in self.connectors:
                errors.append(
                    f"Connection {i}: to_connector '{conn.to_connector}' not found"
                )
            if conn.cable not in self.cables:
                errors.append(
                    f"Connection {i}: cable '{conn.cable}' not found"
                )
            else:
                cable = self.cables[conn.cable]
                if conn.core >= cable.wirecount:
                    errors.append(
                        f"Connection {i}: core index {conn.core} out of range "
                        f"for cable '{conn.cable}' with {cable.wirecount} wires"
                    )

        if errors:
            raise ValueError(
                "Invalid connection references:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        return self

    def get_connector(self, connector_id: str) -> Optional[Connector]:
        """Get a connector by ID.

        Args:
            connector_id: The connector ID to look up.

        Returns:
            The Connector or None if not found.
        """
        return self.connectors.get(connector_id)

    def get_cable(self, cable_id: str) -> Optional[Cable]:
        """Get a cable by ID.

        Args:
            cable_id: The cable ID to look up.

        Returns:
            The Cable or None if not found.
        """
        return self.cables.get(cable_id)

    def get_part(self, part_id: str) -> Optional[Part]:
        """Get a part by ID.

        Args:
            part_id: The part ID to look up.

        Returns:
            The Part or None if not found.
        """
        return self.parts.get(part_id)

    def get_connections_for_connector(self, connector_id: str) -> List[Connection]:
        """Get all connections involving a specific connector.

        Args:
            connector_id: The connector ID to search for.

        Returns:
            List of connections involving the specified connector.
        """
        return [
            conn
            for conn in self.connections
            if conn.from_connector == connector_id or conn.to_connector == connector_id
        ]

    def get_connections_for_cable(self, cable_id: str) -> List[Connection]:
        """Get all connections using a specific cable.

        Args:
            cable_id: The cable ID to search for.

        Returns:
            List of connections using the specified cable.
        """
        return [conn for conn in self.connections if conn.cable == cable_id]

    def get_all_component_ids(self) -> Dict[str, List[str]]:
        """Get all component IDs organized by type.

        Returns:
            Dictionary with 'connectors', 'cables', and 'parts' keys,
            each containing a list of IDs.
        """
        return {
            "connectors": list(self.connectors.keys()),
            "cables": list(self.cables.keys()),
            "parts": list(self.parts.keys()),
        }

    def validate_complete(self) -> List[str]:
        """Perform comprehensive validation of the document.

        Returns:
            List of validation warnings/issues (empty if fully valid).
        """
        issues: List[str] = []

        # Check for unused cables
        used_cables = {conn.cable for conn in self.connections}
        for cable_id in self.cables:
            if cable_id not in used_cables:
                issues.append(f"Cable '{cable_id}' has no connections")

        # Check for unused connectors
        used_connectors = set()
        for conn in self.connections:
            used_connectors.add(conn.from_connector)
            used_connectors.add(conn.to_connector)
        for connector_id in self.connectors:
            if connector_id not in used_connectors:
                issues.append(f"Connector '{connector_id}' has no connections")

        # Check for cables with unused cores
        cable_core_usage: Dict[str, set] = {cable_id: set() for cable_id in self.cables}
        for conn in self.connections:
            if conn.cable in cable_core_usage:
                cable_core_usage[conn.cable].add(conn.core)

        for cable_id, used_cores in cable_core_usage.items():
            cable = self.cables[cable_id]
            all_cores = set(range(cable.wirecount))
            unused_cores = all_cores - used_cores
            if unused_cores:
                issues.append(
                    f"Cable '{cable_id}' has unused cores: {sorted(unused_cores)}"
                )

        return issues
