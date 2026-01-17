"""Tests for data models."""

import pytest
from pydantic import ValidationError

from wireviz_doc.models.document import DocumentMeta, HarnessDocument
from wireviz_doc.models.components import Connector, Cable, Core
from wireviz_doc.models.connections import Connection
from wireviz_doc.models.base import ColorSpec


class TestDocumentMeta:
    """Tests for DocumentMeta model."""

    def test_minimal_valid_metadata(self):
        """Test creating metadata with only required fields."""
        meta = DocumentMeta(
            id="TEST-001",
            title="Test Harness",
            revision="A",
            date="2026-01-17",
        )
        assert meta.id == "TEST-001"
        assert meta.title == "Test Harness"
        assert meta.revision == "A"
        # Optional fields should be None or defaults
        assert meta.author is None
        assert meta.checker is None
        assert meta.approver is None
        assert meta.scale == "NTS"
        assert meta.units == "mm"
        assert meta.sheet == 1
        assert meta.total_sheets == 1

    def test_full_metadata(self):
        """Test creating metadata with all fields."""
        meta = DocumentMeta(
            id="TEST-002",
            title="Full Test Harness",
            revision="B",
            date="2026-01-17",
            author="Test Author",
            checker="Test Checker",
            approver="Test Approver",
            company="Test Company",
            department="Engineering",
            client="Test Client",
            project="Test Project",
            description="A test harness description",
            scale="1:1",
            units="in",
            sheet=2,
            total_sheets=5,
            custom_fields={"custom_key": "custom_value"},
        )
        assert meta.author == "Test Author"
        assert meta.checker == "Test Checker"
        assert meta.client == "Test Client"
        assert meta.scale == "1:1"
        assert meta.custom_fields["custom_key"] == "custom_value"

    def test_required_fields_validation(self):
        """Test that required fields raise errors when missing."""
        with pytest.raises(ValidationError):
            DocumentMeta(title="Missing ID", revision="A", date="2026-01-17")

        with pytest.raises(ValidationError):
            DocumentMeta(id="X", revision="A", date="2026-01-17")  # missing title

    def test_date_parsing(self):
        """Test various date formats are accepted."""
        # ISO format
        meta1 = DocumentMeta(id="X", title="T", revision="A", date="2026-01-17")
        assert meta1.get_date_string() == "2026-01-17"

        # Slash format
        meta2 = DocumentMeta(id="X", title="T", revision="A", date="2026/01/17")
        assert "2026" in meta2.get_date_string()

    def test_whitespace_stripping(self):
        """Test that whitespace is stripped from string fields."""
        meta = DocumentMeta(
            id="  TEST-003  ",
            title="  Whitespace Test  ",
            revision="  A  ",
            date="2026-01-17",
            author="  Author Name  ",
        )
        assert meta.id == "TEST-003"
        assert meta.title == "Whitespace Test"
        assert meta.author == "Author Name"


class TestColorSpec:
    """Tests for ColorSpec model."""

    def test_standard_colors(self):
        """Test standard color codes."""
        colors = ["BK", "WH", "RD", "GN", "BU", "YE", "OG", "BN", "VT", "GY", "PK"]
        for color in colors:
            spec = ColorSpec(code=color)
            assert spec.code == color
            assert spec.display_color == color

    def test_stripe_colors(self):
        """Test stripe color codes (e.g., BU-WH)."""
        spec = ColorSpec(code="BU-WH")
        assert spec.code == "BU-WH"
        assert spec.display_color == "BU-WH"


class TestConnector:
    """Tests for Connector model."""

    def test_basic_connector(self):
        """Test creating a basic connector."""
        conn = Connector(pincount=4)
        assert conn.pincount == 4

    def test_connector_with_pinlabels(self):
        """Test connector with pin labels."""
        conn = Connector(
            pincount=4,
            pinlabels=["VCC", "GND", "TX", "RX"],
        )
        assert len(conn.pinlabels) == 4
        assert conn.pinlabels[0] == "VCC"


class TestCable:
    """Tests for Cable model."""

    def test_basic_cable(self):
        """Test creating a basic cable."""
        cable = Cable(wirecount=4, gauge="22 AWG")
        assert cable.wirecount == 4
        assert cable.gauge == "22 AWG"

    def test_cable_with_cores(self):
        """Test cable with core definitions."""
        cable = Cable(
            wirecount=2,
            gauge="22 AWG",
            cores=[
                Core(index=1, color=ColorSpec(code="RD"), label="VCC"),
                Core(index=2, color=ColorSpec(code="BK"), label="GND"),
            ],
        )
        assert len(cable.cores) == 2
        assert cable.cores[0].label == "VCC"


class TestConnection:
    """Tests for Connection model."""

    def test_basic_connection(self):
        """Test creating a basic connection."""
        conn = Connection(
            from_connector="J1",
            from_pin=1,
            cable="W1",
            core=0,
            to_connector="J2",
            to_pin=1,
        )
        assert conn.from_connector == "J1"
        assert conn.to_connector == "J2"
        assert conn.cable == "W1"


class TestHarnessDocument:
    """Tests for HarnessDocument model."""

    def test_minimal_document(self):
        """Test creating a minimal harness document."""
        doc = HarnessDocument(
            metadata=DocumentMeta(
                id="TEST-001",
                title="Minimal Test",
                revision="A",
                date="2026-01-17",
            ),
        )
        assert doc.metadata.id == "TEST-001"
        assert len(doc.connectors) == 0
        assert len(doc.cables) == 0
        assert len(doc.connections) == 0

    def test_document_with_components(self):
        """Test document with connectors and cables."""
        doc = HarnessDocument(
            metadata=DocumentMeta(
                id="TEST-002",
                title="Component Test",
                revision="A",
                date="2026-01-17",
            ),
            connectors={
                "J1": Connector(pincount=2, pinlabels=["VCC", "GND"]),
                "J2": Connector(pincount=2, pinlabels=["VCC", "GND"]),
            },
            cables={
                "W1": Cable(wirecount=2, gauge="22 AWG"),
            },
            connections=[
                Connection(from_connector="J1", from_pin=1, cable="W1", core=0, to_connector="J2", to_pin=1),
                Connection(from_connector="J1", from_pin=2, cable="W1", core=1, to_connector="J2", to_pin=2),
            ],
        )
        assert len(doc.connectors) == 2
        assert len(doc.cables) == 1
        assert len(doc.connections) == 2

    def test_invalid_connection_reference(self):
        """Test that invalid connection references raise errors."""
        with pytest.raises(ValidationError):
            HarnessDocument(
                metadata=DocumentMeta(
                    id="TEST-003",
                    title="Invalid Test",
                    revision="A",
                    date="2026-01-17",
                ),
                connectors={"J1": Connector(pincount=2)},
                cables={"W1": Cable(wirecount=2, gauge="22 AWG")},
                connections=[
                    # J2 doesn't exist
                    Connection(from_connector="J1", from_pin=1, cable="W1", core=0, to_connector="J2", to_pin=1),
                ],
            )
