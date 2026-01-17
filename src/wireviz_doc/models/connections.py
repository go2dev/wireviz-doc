"""Connection models for WireViz document pipeline.

This module defines Pydantic models for representing electrical connections
between connectors through cables in a wire harness. Connections specify
how pins on connectors are wired through specific cable cores.
"""

from __future__ import annotations

from typing import Any, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Connection(BaseModel):
    """Represents a single electrical connection in a wire harness.

    A Connection defines how a pin on one connector connects to a pin on
    another connector through a specific core (wire) of a cable. This is
    the fundamental wiring specification in a harness document.

    Attributes:
        from_connector: ID of the source connector.
        from_pin: Pin number or label on the source connector.
        cable: ID of the cable carrying this connection.
        core: Index of the cable core (wire) used for this connection.
        to_connector: ID of the destination connector.
        to_pin: Pin number or label on the destination connector.
        notes: Optional notes about this specific connection.
        signal_name: Optional signal name for documentation.
        wire_label: Optional custom label for this wire run.

    Example:
        >>> conn = Connection(
        ...     from_connector="J1",
        ...     from_pin=1,
        ...     cable="W1",
        ...     core=0,
        ...     to_connector="J2",
        ...     to_pin="A"
        ... )
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    from_connector: str = Field(..., description="ID of the source connector")
    from_pin: Union[int, str] = Field(
        ..., description="Pin number or label on source connector"
    )
    cable: str = Field(..., description="ID of the cable carrying this connection")
    core: int = Field(
        ..., ge=0, description="Index of cable core (wire) for this connection"
    )
    to_connector: str = Field(..., description="ID of the destination connector")
    to_pin: Union[int, str] = Field(
        ..., description="Pin number or label on destination connector"
    )
    notes: Optional[str] = Field(
        default=None, description="Optional notes about this connection"
    )
    signal_name: Optional[str] = Field(
        default=None, description="Optional signal name for documentation"
    )
    wire_label: Optional[str] = Field(
        default=None, description="Optional custom label for this wire run"
    )

    @field_validator("from_connector", "cable", "to_connector")
    @classmethod
    def validate_id_not_empty(cls, v: str, info: Any) -> str:
        """Ensure ID fields are not empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()

    @field_validator("from_pin", "to_pin", mode="before")
    @classmethod
    def normalize_pin(cls, v: Union[int, str]) -> Union[int, str]:
        """Normalize pin specification."""
        if isinstance(v, int):
            if v < 1:
                raise ValueError("Pin numbers must be positive (1-based)")
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Pin label cannot be empty")
            # Try to convert numeric strings to integers
            try:
                int_val = int(v)
                if int_val < 1:
                    raise ValueError("Pin numbers must be positive (1-based)")
                return int_val
            except ValueError:
                # Keep as string label
                return v
        raise ValueError(f"Invalid pin specification: {v!r}")

    @field_validator("notes", "signal_name", "wire_label", mode="before")
    @classmethod
    def strip_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace from optional string fields."""
        if v is None:
            return None
        v = str(v).strip()
        return v if v else None

    def __str__(self) -> str:
        """Return a human-readable representation of the connection."""
        return (
            f"{self.from_connector}:{self.from_pin} -> "
            f"[{self.cable}:{self.core}] -> "
            f"{self.to_connector}:{self.to_pin}"
        )


class ConnectionGroup(BaseModel):
    """Represents a logical group of related connections.

    Connection groups allow organizing connections by function, subsystem,
    or other logical groupings for documentation and organization purposes.

    Attributes:
        name: Name of this connection group.
        description: Optional description of the group's purpose.
        connections: List of connections in this group.
        color_code: Optional color code for visual grouping in diagrams.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    name: str = Field(..., description="Name of this connection group")
    description: Optional[str] = Field(
        default=None, description="Description of the group's purpose"
    )
    connections: List[Connection] = Field(
        default_factory=list, description="Connections in this group"
    )
    color_code: Optional[str] = Field(
        default=None, description="Color code for visual grouping"
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Ensure name is not empty."""
        if not v or not v.strip():
            raise ValueError("Connection group name cannot be empty")
        return v.strip()

    def add_connection(self, connection: Connection) -> None:
        """Add a connection to this group.

        Args:
            connection: The connection to add.
        """
        self.connections.append(connection)

    def get_connections_for_connector(self, connector_id: str) -> List[Connection]:
        """Get all connections involving a specific connector.

        Args:
            connector_id: The connector ID to search for.

        Returns:
            List of connections that involve the specified connector.
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
            List of connections that use the specified cable.
        """
        return [conn for conn in self.connections if conn.cable == cable_id]


class SpliceConnection(BaseModel):
    """Represents a splice point where multiple wires connect together.

    Splices are junction points where multiple wires are joined without
    a traditional connector, often using crimp splices, solder joints,
    or other joining methods.

    Attributes:
        id: Unique identifier for this splice point.
        incoming: List of connections coming into the splice.
        outgoing: List of connections going out from the splice.
        splice_type: Type of splice (e.g., 'butt', 'inline', 'branch').
        notes: Optional notes about the splice.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    id: str = Field(..., description="Unique identifier for this splice point")
    incoming: List[Connection] = Field(
        default_factory=list, description="Connections coming into splice"
    )
    outgoing: List[Connection] = Field(
        default_factory=list, description="Connections going out from splice"
    )
    splice_type: Optional[str] = Field(
        default=None, description="Type of splice (butt, inline, branch)"
    )
    notes: Optional[str] = Field(default=None, description="Optional notes")

    @field_validator("id")
    @classmethod
    def validate_id_not_empty(cls, v: str) -> str:
        """Ensure ID is not empty."""
        if not v or not v.strip():
            raise ValueError("Splice ID cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_has_connections(self) -> SpliceConnection:
        """Validate that splice has at least some connections."""
        if not self.incoming and not self.outgoing:
            raise ValueError(
                "Splice must have at least one incoming or outgoing connection"
            )
        return self
