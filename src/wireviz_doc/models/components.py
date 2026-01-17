"""Harness component models for WireViz document pipeline.

This module defines Pydantic models for the main components of a wire harness:
connectors, cables, and their constituent parts like cores (individual wires).
These models extend the basic Part concept with component-specific attributes.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from wireviz_doc.models.base import ColorSpec, ImageSpec, Quantity
from wireviz_doc.models.parts import Accessory, AlternatePart


class ConnectorType(str, Enum):
    """Enumeration of common connector types."""

    RECTANGULAR = "rectangular"
    CIRCULAR = "circular"
    MODULAR = "modular"
    TERMINAL_BLOCK = "terminal_block"
    SPLICE = "splice"
    BLADE = "blade"
    RING = "ring"
    SPADE = "spade"
    BULLET = "bullet"
    PIN_HEADER = "pin_header"
    USB = "usb"
    D_SUB = "d_sub"
    AUTOMOTIVE = "automotive"
    WIRE_TO_BOARD = "wire_to_board"
    WIRE_TO_WIRE = "wire_to_wire"
    OTHER = "other"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value


class ShieldType(str, Enum):
    """Enumeration of cable shield types."""

    BRAIDED = "braided"
    FOIL = "foil"
    SPIRAL = "spiral"
    BRAIDED_FOIL = "braided_foil"
    NONE = "none"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value


class Core(BaseModel):
    """Represents a single wire core within a cable.

    A core is an individual conductor within a multi-conductor cable.
    It has a position index, color coding, and optional labeling.

    Attributes:
        index: Zero-based index of this core within the cable.
        color: Color specification for wire identification.
        label: Optional custom label for this core (e.g., "GND", "+12V").
        pair_group: Optional pair group identifier for twisted pairs.
        twist_spec: Optional twist specification (e.g., "pair1", "quad1").
        gauge: Optional individual core gauge if different from cable default.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    index: int = Field(..., ge=0, description="Zero-based index of core in cable")
    color: ColorSpec = Field(..., description="Color specification for identification")
    label: Optional[str] = Field(
        default=None, description="Custom label (e.g., 'GND', '+12V')"
    )
    pair_group: Optional[str] = Field(
        default=None, description="Pair group identifier for twisted pairs"
    )
    twist_spec: Optional[str] = Field(
        default=None, description="Twist specification (e.g., 'pair1', 'quad1')"
    )
    gauge: Optional[str] = Field(
        default=None, description="Individual core gauge if different from cable default"
    )

    @field_validator("color", mode="before")
    @classmethod
    def parse_color(cls, v: Union[str, ColorSpec, Dict[str, Any]]) -> ColorSpec:
        """Parse color from string or dict to ColorSpec."""
        if isinstance(v, ColorSpec):
            return v
        if isinstance(v, str):
            return ColorSpec.parse(v)
        if isinstance(v, dict):
            return ColorSpec(**v)
        raise ValueError(f"Invalid color specification: {v!r}")

    @field_validator("label", "pair_group", "twist_spec", "gauge", mode="before")
    @classmethod
    def strip_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace from optional string fields."""
        if v is None:
            return None
        v = str(v).strip()
        return v if v else None


class PinDefinition(BaseModel):
    """Detailed definition of a single connector pin.

    Provides comprehensive pin information beyond just a label,
    including electrical characteristics and connection type.

    Attributes:
        number: Pin number or position identifier.
        label: Pin label or signal name.
        type: Pin type (e.g., 'signal', 'power', 'ground', 'nc').
        color: Optional color coding for the pin.
        notes: Optional notes about the pin.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    number: Union[int, str] = Field(..., description="Pin number or position identifier")
    label: Optional[str] = Field(default=None, description="Pin label or signal name")
    type: Optional[str] = Field(
        default=None, description="Pin type (signal, power, ground, nc)"
    )
    color: Optional[ColorSpec] = Field(default=None, description="Optional pin color")
    notes: Optional[str] = Field(default=None, description="Optional notes")

    @field_validator("color", mode="before")
    @classmethod
    def parse_color(
        cls, v: Optional[Union[str, ColorSpec, Dict[str, Any]]]
    ) -> Optional[ColorSpec]:
        """Parse color from string or dict to ColorSpec."""
        if v is None:
            return None
        if isinstance(v, ColorSpec):
            return v
        if isinstance(v, str):
            return ColorSpec.parse(v)
        if isinstance(v, dict):
            return ColorSpec(**v)
        raise ValueError(f"Invalid color specification: {v!r}")


class ShieldSpec(BaseModel):
    """Specification for cable shielding.

    Attributes:
        type: Type of shield (braided, foil, etc.).
        coverage: Optional coverage percentage for braided shields.
        drain_wire: Whether shield has a drain wire.
        color: Optional color of drain wire if present.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    type: ShieldType = Field(..., description="Type of shielding")
    coverage: Optional[float] = Field(
        default=None, ge=0, le=100, description="Coverage percentage for braided shields"
    )
    drain_wire: bool = Field(default=False, description="Whether shield has drain wire")
    color: Optional[ColorSpec] = Field(
        default=None, description="Color of drain wire if present"
    )

    @field_validator("color", mode="before")
    @classmethod
    def parse_color(
        cls, v: Optional[Union[str, ColorSpec, Dict[str, Any]]]
    ) -> Optional[ColorSpec]:
        """Parse color from string or dict to ColorSpec."""
        if v is None:
            return None
        if isinstance(v, ColorSpec):
            return v
        if isinstance(v, str):
            return ColorSpec.parse(v)
        if isinstance(v, dict):
            return ColorSpec(**v)
        raise ValueError(f"Invalid color specification: {v!r}")


class Connector(BaseModel):
    """Represents a connector component in a wire harness.

    Extends the Part concept with connector-specific attributes including
    pin configuration, mating information, and terminal specifications.

    Attributes:
        id: Unique identifier for this connector within the document.
        primary_pn: Primary internal part number.
        manufacturer: Connector manufacturer name.
        mpn: Manufacturer Part Number.
        description: Human-readable connector description.
        type: Connector type category.
        subtype: Optional connector subtype or series.
        pincount: Number of pins/contacts in the connector.
        pinlabels: List of pin labels in order.
        pins: Optional detailed pin definitions.
        alternates: List of acceptable alternate connectors.
        fields: Additional custom fields.
        image: Optional connector image.
        additional_components: Associated accessories (terminals, seals, etc.).
        notes: Optional notes about the connector.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
        extra="forbid",
    )

    id: str = Field(..., description="Unique identifier for this connector")
    primary_pn: str = Field(
        ..., description="Primary internal part number", alias="primaryPN"
    )
    manufacturer: str = Field(..., description="Connector manufacturer name")
    mpn: str = Field(..., description="Manufacturer Part Number")
    description: str = Field(..., description="Human-readable description")
    type: ConnectorType = Field(..., description="Connector type category")
    subtype: Optional[str] = Field(
        default=None, description="Connector subtype or series"
    )
    pincount: int = Field(..., ge=1, description="Number of pins/contacts")
    pinlabels: List[str] = Field(
        default_factory=list, description="Pin labels in order"
    )
    pins: Optional[List[PinDefinition]] = Field(
        default=None, description="Detailed pin definitions"
    )
    alternates: List[AlternatePart] = Field(
        default_factory=list, description="Acceptable alternate connectors"
    )
    fields: Dict[str, Any] = Field(
        default_factory=dict, description="Additional custom fields"
    )
    image: Optional[ImageSpec] = Field(default=None, description="Connector image")
    additional_components: List[Accessory] = Field(
        default_factory=list, description="Associated accessories"
    )
    notes: Optional[str] = Field(default=None, description="Optional notes")

    @field_validator("id", "primary_pn", "manufacturer", "mpn", "description")
    @classmethod
    def validate_required_strings(cls, v: str, info: Any) -> str:
        """Ensure required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_pinlabels_count(self) -> Connector:
        """Validate that pinlabels count matches pincount if provided."""
        if self.pinlabels and len(self.pinlabels) != self.pincount:
            raise ValueError(
                f"pinlabels count ({len(self.pinlabels)}) must match "
                f"pincount ({self.pincount})"
            )
        return self

    @model_validator(mode="after")
    def validate_pins_count(self) -> Connector:
        """Validate that pins count matches pincount if provided."""
        if self.pins and len(self.pins) != self.pincount:
            raise ValueError(
                f"pins count ({len(self.pins)}) must match pincount ({self.pincount})"
            )
        return self

    def get_pin_label(self, pin_number: int) -> Optional[str]:
        """Get the label for a specific pin number (1-based).

        Args:
            pin_number: The pin number (1-based indexing).

        Returns:
            The pin label or None if not defined.
        """
        if not self.pinlabels:
            return None
        if 1 <= pin_number <= len(self.pinlabels):
            return self.pinlabels[pin_number - 1]
        return None


class Cable(BaseModel):
    """Represents a cable component in a wire harness.

    Extends the Part concept with cable-specific attributes including
    wire count, core definitions, gauge, and shielding specifications.

    Attributes:
        id: Unique identifier for this cable within the document.
        primary_pn: Primary internal part number.
        manufacturer: Cable manufacturer name.
        mpn: Manufacturer Part Number.
        description: Human-readable cable description.
        wirecount: Number of conductors/wires in the cable.
        cores: List of core (individual wire) definitions.
        gauge: Wire gauge specification (e.g., "22 AWG", "0.5 mm2").
        length: Cable length with unit.
        shield: Optional shield specification.
        alternates: List of acceptable alternate cables.
        fields: Additional custom fields.
        image: Optional cable image.
        additional_components: Associated accessories (conduit, labels, etc.).
        notes: Optional notes about the cable.
        outer_diameter: Optional outer diameter specification.
        jacket_color: Optional jacket/insulation color.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
        extra="forbid",
    )

    id: str = Field(..., description="Unique identifier for this cable")
    primary_pn: str = Field(
        ..., description="Primary internal part number", alias="primaryPN"
    )
    manufacturer: str = Field(..., description="Cable manufacturer name")
    mpn: str = Field(..., description="Manufacturer Part Number")
    description: str = Field(..., description="Human-readable description")
    wirecount: int = Field(..., ge=1, description="Number of conductors/wires")
    cores: List[Core] = Field(
        default_factory=list, description="Core (wire) definitions"
    )
    gauge: str = Field(..., description="Wire gauge (e.g., '22 AWG', '0.5 mm2')")
    length: Quantity = Field(..., description="Cable length with unit")
    shield: Optional[ShieldSpec] = Field(
        default=None, description="Shield specification"
    )
    alternates: List[AlternatePart] = Field(
        default_factory=list, description="Acceptable alternate cables"
    )
    fields: Dict[str, Any] = Field(
        default_factory=dict, description="Additional custom fields"
    )
    image: Optional[ImageSpec] = Field(default=None, description="Cable image")
    additional_components: List[Accessory] = Field(
        default_factory=list, description="Associated accessories"
    )
    notes: Optional[str] = Field(default=None, description="Optional notes")
    outer_diameter: Optional[str] = Field(
        default=None, description="Outer diameter specification"
    )
    jacket_color: Optional[ColorSpec] = Field(
        default=None, description="Jacket/insulation color"
    )

    @field_validator("id", "primary_pn", "manufacturer", "mpn", "description", "gauge")
    @classmethod
    def validate_required_strings(cls, v: str, info: Any) -> str:
        """Ensure required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()

    @field_validator("length", mode="before")
    @classmethod
    def parse_length(cls, v: Union[Quantity, Dict[str, Any]]) -> Quantity:
        """Parse length from dict to Quantity."""
        if isinstance(v, Quantity):
            return v
        if isinstance(v, dict):
            return Quantity(**v)
        raise ValueError(f"Invalid length specification: {v!r}")

    @field_validator("jacket_color", mode="before")
    @classmethod
    def parse_jacket_color(
        cls, v: Optional[Union[str, ColorSpec, Dict[str, Any]]]
    ) -> Optional[ColorSpec]:
        """Parse jacket color from string or dict to ColorSpec."""
        if v is None:
            return None
        if isinstance(v, ColorSpec):
            return v
        if isinstance(v, str):
            return ColorSpec.parse(v)
        if isinstance(v, dict):
            return ColorSpec(**v)
        raise ValueError(f"Invalid color specification: {v!r}")

    @model_validator(mode="after")
    def validate_cores_count(self) -> Cable:
        """Validate that cores count matches wirecount if cores are provided."""
        if self.cores and len(self.cores) != self.wirecount:
            raise ValueError(
                f"cores count ({len(self.cores)}) must match "
                f"wirecount ({self.wirecount})"
            )
        return self

    @model_validator(mode="after")
    def validate_core_indices(self) -> Cable:
        """Validate that core indices are valid and unique."""
        if not self.cores:
            return self

        indices = [core.index for core in self.cores]
        if len(indices) != len(set(indices)):
            raise ValueError("Core indices must be unique")

        for idx in indices:
            if idx < 0 or idx >= self.wirecount:
                raise ValueError(
                    f"Core index {idx} out of range for cable with "
                    f"{self.wirecount} wires"
                )
        return self

    def get_core_by_index(self, index: int) -> Optional[Core]:
        """Get a core by its index.

        Args:
            index: The zero-based index of the core.

        Returns:
            The Core at the given index or None if not found.
        """
        for core in self.cores:
            if core.index == index:
                return core
        return None

    def get_core_by_label(self, label: str) -> Optional[Core]:
        """Get a core by its label.

        Args:
            label: The label of the core to find.

        Returns:
            The Core with the given label or None if not found.
        """
        for core in self.cores:
            if core.label == label:
                return core
        return None
