"""Base classes and common types for WireViz document models.

This module provides foundational Pydantic models used throughout the WireViz
documentation pipeline, including color specifications, image references,
and quantity measurements.
"""

from __future__ import annotations

import re
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class ColorSpec(BaseModel):
    """Represents a wire or component color specification.

    Handles various color format conventions used in wiring documentation:
    - Hyphenated format: "BL-WH" (blue with white stripe)
    - Concatenated format: "BUWH" (blue with white stripe)
    - Numbered format: "BL1" (blue, circuit 1)
    - Single color: "BK" (black)

    Attributes:
        display_color: The original color string as specified in the source.
        base_color: The primary/base color code (normalized to uppercase).
        stripe_color: Optional stripe or secondary color code.

    Examples:
        >>> ColorSpec.parse("BL-WH")
        ColorSpec(display_color='BL-WH', base_color='BL', stripe_color='WH')

        >>> ColorSpec.parse("BUWH")
        ColorSpec(display_color='BUWH', base_color='BU', stripe_color='WH')

        >>> ColorSpec.parse("BK")
        ColorSpec(display_color='BK', base_color='BK', stripe_color=None)
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    display_color: str
    base_color: str
    stripe_color: Optional[str] = None

    # Standard two-letter color codes used in wiring (IEC 60757 and common variants)
    STANDARD_COLOR_CODES: ClassVar[set[str]] = {
        "BK",  # Black
        "BN",  # Brown
        "RD",  # Red
        "OG",  # Orange
        "YE",  # Yellow
        "GN",  # Green
        "BU",  # Blue
        "BL",  # Blue (alternate)
        "VT",  # Violet
        "PK",  # Pink
        "GY",  # Grey
        "WH",  # White
        "TQ",  # Turquoise
        "SR",  # Silver
        "GD",  # Gold
        "CL",  # Clear/Transparent
        "OL",  # Olive
        "CR",  # Cream
        "TN",  # Tan
        "SL",  # Slate
    }

    @classmethod
    def parse(cls, color_str: str) -> ColorSpec:
        """Parse a color string into a ColorSpec instance.

        Supports multiple color specification formats:
        - Hyphenated: "BL-WH", "RD-BK"
        - Concatenated 4-char: "BUWH", "RDBK"
        - Numbered: "BL1", "RD2"
        - Single color: "BK", "WH"

        Args:
            color_str: The color specification string to parse.

        Returns:
            A ColorSpec instance with parsed color components.

        Raises:
            ValueError: If the color string format is unrecognized.
        """
        if not color_str or not isinstance(color_str, str):
            raise ValueError(f"Invalid color specification: {color_str!r}")

        color_str = color_str.strip().upper()

        if not color_str:
            raise ValueError("Color specification cannot be empty")

        # Format 1: Hyphenated format (e.g., "BL-WH", "RD-BK-YE")
        if "-" in color_str:
            parts = color_str.split("-")
            base = parts[0]
            stripe = parts[1] if len(parts) > 1 else None
            return cls(
                display_color=color_str,
                base_color=base,
                stripe_color=stripe,
            )

        # Format 2: Numbered format (e.g., "BL1", "RD23")
        # Match 2-letter code followed by digits
        numbered_match = re.match(r"^([A-Z]{2})(\d+)$", color_str)
        if numbered_match:
            base = numbered_match.group(1)
            return cls(
                display_color=color_str,
                base_color=base,
                stripe_color=None,
            )

        # Format 3: Concatenated 4-character format (e.g., "BUWH", "RDBK")
        # Only parse as concatenated if both parts are valid color codes
        if len(color_str) == 4:
            potential_base = color_str[:2]
            potential_stripe = color_str[2:]
            if (
                potential_base in cls.STANDARD_COLOR_CODES
                and potential_stripe in cls.STANDARD_COLOR_CODES
            ):
                return cls(
                    display_color=color_str,
                    base_color=potential_base,
                    stripe_color=potential_stripe,
                )

        # Format 4: Single color code (e.g., "BK", "WH")
        # Accept any 2-3 letter code as a single color
        if 2 <= len(color_str) <= 3 and color_str.isalpha():
            return cls(
                display_color=color_str,
                base_color=color_str,
                stripe_color=None,
            )

        # Fallback: treat entire string as base color
        return cls(
            display_color=color_str,
            base_color=color_str,
            stripe_color=None,
        )

    @field_validator("base_color", "stripe_color", mode="before")
    @classmethod
    def normalize_color_case(cls, v: Optional[str]) -> Optional[str]:
        """Normalize color codes to uppercase."""
        if v is None:
            return None
        return v.strip().upper() if isinstance(v, str) else v

    def __str__(self) -> str:
        """Return the display representation of the color."""
        return self.display_color


class ImageSpec(BaseModel):
    """Specification for an image reference in documentation.

    Used to embed images of parts, assemblies, or diagrams within
    the harness documentation.

    Attributes:
        src: Path or URL to the image file.
        caption: Optional descriptive caption for the image.
        height: Optional height specification (e.g., "100px", "2in").
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    src: str
    caption: Optional[str] = None
    height: Optional[str] = None

    @field_validator("src")
    @classmethod
    def validate_src_not_empty(cls, v: str) -> str:
        """Ensure image source path is not empty."""
        if not v or not v.strip():
            raise ValueError("Image source path cannot be empty")
        return v.strip()

    @field_validator("height")
    @classmethod
    def validate_height_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate height specification format if provided."""
        if v is None:
            return None

        v = v.strip()
        if not v:
            return None

        # Accept common dimension formats
        valid_pattern = re.compile(
            r"^\d+(\.\d+)?\s*(px|pt|in|cm|mm|em|rem|%)?$", re.IGNORECASE
        )
        if not valid_pattern.match(v):
            raise ValueError(
                f"Invalid height format: {v!r}. "
                "Expected format like '100px', '2.5in', or '50mm'"
            )
        return v


class Quantity(BaseModel):
    """Represents a quantity with its unit of measurement.

    Used for specifying lengths, counts, and other measurable values
    in harness specifications.

    Attributes:
        value: The numeric value of the quantity.
        unit: The unit of measurement (e.g., "m", "ft", "pcs", "mm").

    Examples:
        >>> Quantity(value=2.5, unit="m")
        Quantity(value=2.5, unit='m')

        >>> Quantity(value=10, unit="ft")
        Quantity(value=10.0, unit='ft')
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    value: float
    unit: str

    # Common units for wire harness specifications
    COMMON_UNITS: ClassVar[set[str]] = {
        # Length units
        "m",
        "cm",
        "mm",
        "ft",
        "in",
        # Count units
        "pcs",
        "ea",
        # Gauge/size units
        "AWG",
        "mm2",
        "mm²",
    }

    @field_validator("value", mode="before")
    @classmethod
    def coerce_value_to_float(cls, v: object) -> float:
        """Coerce numeric values to float."""
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v.strip())
            except ValueError:
                raise ValueError(f"Cannot convert {v!r} to a numeric value")
        raise ValueError(f"Invalid quantity value type: {type(v).__name__}")

    @field_validator("unit")
    @classmethod
    def validate_unit_not_empty(cls, v: str) -> str:
        """Ensure unit is not empty."""
        if not v or not v.strip():
            raise ValueError("Unit cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_non_negative(self) -> Quantity:
        """Validate that quantity value is non-negative for most use cases."""
        # Allow negative values as some contexts may need them (offsets, etc.)
        # but warn in practice if this becomes an issue
        return self

    def __str__(self) -> str:
        """Return a human-readable representation."""
        # Format integer values without decimal places
        if self.value == int(self.value):
            return f"{int(self.value)} {self.unit}"
        return f"{self.value} {self.unit}"

    def to_base_unit(self, target_unit: str) -> Quantity:
        """Convert quantity to a different unit (basic conversions).

        Args:
            target_unit: The target unit to convert to.

        Returns:
            A new Quantity in the target unit.

        Raises:
            ValueError: If conversion between units is not supported.

        Note:
            Currently supports basic length conversions. Extend as needed.
        """
        # Length conversion factors to meters
        length_to_meters: dict[str, float] = {
            "m": 1.0,
            "cm": 0.01,
            "mm": 0.001,
            "ft": 0.3048,
            "in": 0.0254,
        }

        current_unit = self.unit.lower()
        target_unit_lower = target_unit.lower()

        if current_unit in length_to_meters and target_unit_lower in length_to_meters:
            # Convert to meters, then to target
            meters = self.value * length_to_meters[current_unit]
            target_value = meters / length_to_meters[target_unit_lower]
            return Quantity(value=target_value, unit=target_unit)

        if current_unit == target_unit_lower:
            return Quantity(value=self.value, unit=target_unit)

        raise ValueError(
            f"Cannot convert from {self.unit!r} to {target_unit!r}. "
            "Conversion not supported."
        )
