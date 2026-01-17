"""Part-related models for WireViz document pipeline.

This module defines Pydantic models for parts, alternate parts, and accessories
used in wire harness documentation. Parts represent physical components with
manufacturer information, part numbers, and optional alternates.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from wireviz_doc.models.base import ImageSpec, Quantity


class AccessoryType(str, Enum):
    """Enumeration of accessory types used in wire harness assemblies.

    These represent additional components that may be applied to cables,
    connectors, or connection points in a harness.
    """

    HEATSHRINK = "heatshrink"
    LABEL_SLEEVE = "label_sleeve"
    CONDUIT = "conduit"
    BRAID = "braid"
    TAPE = "tape"
    GROMMET = "grommet"
    CLAMP = "clamp"
    TIE_WRAP = "tie_wrap"
    FERRULE = "ferrule"
    BOOT = "boot"
    OTHER = "other"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value


class AlternatePart(BaseModel):
    """Represents an alternate/substitute part for a primary component.

    Alternate parts provide sourcing flexibility by documenting equivalent
    parts from different manufacturers or vendors.

    Attributes:
        manufacturer: Name of the alternate part manufacturer.
        mpn: Manufacturer Part Number for the alternate.
        vendor_sku: Optional vendor-specific SKU or ordering code.
        url: Optional URL to datasheet or product page.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    manufacturer: str
    mpn: str = Field(..., description="Manufacturer Part Number")
    vendor_sku: Optional[str] = Field(
        default=None, description="Vendor-specific SKU or ordering code"
    )
    url: Optional[str] = Field(
        default=None, description="URL to datasheet or product page"
    )

    @field_validator("manufacturer", "mpn")
    @classmethod
    def validate_not_empty(cls, v: str, info: Any) -> str:
        """Ensure required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()

    @field_validator("url")
    @classmethod
    def validate_url_format(cls, v: Optional[str]) -> Optional[str]:
        """Basic validation for URL format if provided."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        # Basic URL validation - must start with http:// or https://
        if not v.startswith(("http://", "https://")):
            raise ValueError(
                f"Invalid URL format: {v!r}. URL must start with http:// or https://"
            )
        return v


class Part(BaseModel):
    """Represents a physical part or component used in a wire harness.

    A Part contains all the information needed to identify, source, and
    document a component including manufacturer details, part numbers,
    descriptions, and optional alternates.

    Attributes:
        id: Unique identifier for this part within the document.
        primary_pn: Primary internal part number (company PN or reference).
        manufacturer: Name of the primary manufacturer.
        mpn: Manufacturer Part Number.
        description: Human-readable description of the part.
        alternates: List of acceptable alternate/substitute parts.
        fields: Additional custom fields as key-value pairs.
        image: Optional image specification for the part.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
        extra="forbid",
    )

    id: str = Field(..., description="Unique identifier for this part")
    primary_pn: str = Field(
        ..., description="Primary internal part number", alias="primaryPN"
    )
    manufacturer: str = Field(..., description="Primary manufacturer name")
    mpn: str = Field(..., description="Manufacturer Part Number")
    description: str = Field(..., description="Human-readable part description")
    alternates: List[AlternatePart] = Field(
        default_factory=list, description="List of acceptable alternate parts"
    )
    fields: Dict[str, Any] = Field(
        default_factory=dict, description="Additional custom fields"
    )
    image: Optional[ImageSpec] = Field(
        default=None, description="Optional image of the part"
    )

    @field_validator("id", "primary_pn", "manufacturer", "mpn", "description")
    @classmethod
    def validate_required_strings(cls, v: str, info: Any) -> str:
        """Ensure required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Validate that ID follows acceptable format (alphanumeric with limited special chars)."""
        v = v.strip()
        # Allow alphanumeric, hyphens, underscores, and periods
        import re

        if not re.match(r"^[a-zA-Z0-9_\-.]+$", v):
            raise ValueError(
                f"Invalid ID format: {v!r}. "
                "ID must contain only alphanumeric characters, hyphens, underscores, and periods."
            )
        return v

    def get_field(self, key: str, default: Any = None) -> Any:
        """Get a custom field value by key.

        Args:
            key: The field key to retrieve.
            default: Default value if key is not found.

        Returns:
            The field value or default.
        """
        return self.fields.get(key, default)


class Accessory(BaseModel):
    """Represents an accessory applied to a cable, connector, or connection.

    Accessories are supplementary components like heat shrink tubing,
    labels, conduit, or braided sleeving that are applied during assembly.

    Attributes:
        type: The type/category of accessory.
        part: Reference to the Part definition for this accessory.
        quantity: The quantity required (with unit).
        location: Optional description of where the accessory is applied.
        notes: Optional assembly or application notes.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    type: AccessoryType = Field(..., description="Type/category of accessory")
    part: Part = Field(..., description="Part definition for this accessory")
    quantity: Quantity = Field(..., description="Quantity required with unit")
    location: Optional[str] = Field(
        default=None, description="Description of where accessory is applied"
    )
    notes: Optional[str] = Field(
        default=None, description="Assembly or application notes"
    )

    @field_validator("location", "notes", mode="before")
    @classmethod
    def strip_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace from optional string fields."""
        if v is None:
            return None
        v = str(v).strip()
        return v if v else None


class PartReference(BaseModel):
    """A lightweight reference to a Part by ID.

    Used when the full Part definition is stored elsewhere (e.g., in a
    parts dictionary) and only a reference is needed.

    Attributes:
        part_id: The ID of the referenced part.
        quantity: Optional quantity specification.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        frozen=True,
    )

    part_id: str = Field(..., description="ID of the referenced part")
    quantity: Optional[Quantity] = Field(
        default=None, description="Optional quantity specification"
    )

    @field_validator("part_id")
    @classmethod
    def validate_part_id(cls, v: str) -> str:
        """Ensure part ID is not empty."""
        if not v or not v.strip():
            raise ValueError("part_id cannot be empty")
        return v.strip()
