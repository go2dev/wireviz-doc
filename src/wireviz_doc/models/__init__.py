"""Data models for wireviz-doc.

This package provides Pydantic models for representing wire harness
documentation including components, connections, and metadata.
"""

from wireviz_doc.models.base import ColorSpec, ImageSpec, Quantity
from wireviz_doc.models.components import (
    Cable,
    Connector,
    ConnectorType,
    Core,
    PinDefinition,
    ShieldSpec,
    ShieldType,
)
from wireviz_doc.models.connections import (
    Connection,
    ConnectionGroup,
    SpliceConnection,
)
from wireviz_doc.models.document import DocumentMeta, HarnessDocument
from wireviz_doc.models.parts import (
    Accessory,
    AccessoryType,
    AlternatePart,
    Part,
    PartReference,
)

__all__ = [
    # Base types
    "ColorSpec",
    "ImageSpec",
    "Quantity",
    # Component types
    "Connector",
    "ConnectorType",
    "Cable",
    "Core",
    "PinDefinition",
    "ShieldSpec",
    "ShieldType",
    # Connection types
    "Connection",
    "ConnectionGroup",
    "SpliceConnection",
    # Part types
    "Part",
    "AlternatePart",
    "Accessory",
    "AccessoryType",
    "PartReference",
    # Document types
    "DocumentMeta",
    "HarnessDocument",
]
