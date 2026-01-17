# WireViz Drawing Generator Examples

This directory contains example harness definitions demonstrating the extended
YAML schema used by `wvdoc`.

## Files

| File | Description |
|------|-------------|
| `demo-harness.harness.yml` | Full-featured example showcasing all schema capabilities |
| `simple-harness.harness.yml` | Minimal example showing the bare essentials |
| `parts-library.yml` | Standalone parts library for import/reference |

## Usage

Build the demo harness:

```bash
wvdoc build examples/demo-harness.harness.yml
```

Build all examples:

```bash
wvdoc build "examples/*.harness.yml"
```

Validate without building:

```bash
wvdoc lint examples/demo-harness.harness.yml
```

## Schema Overview

Each `.harness.yml` file follows this structure:

```yaml
metadata:      # Document identification and revision info
parts:         # Parts library (connectors, cables, accessories)
connectors:    # Connector instances referencing parts
cables:        # Cable instances with core definitions
connections:   # Pin-to-pin wiring matrix
accessories:   # Heatshrink, labels, conduit placements
```

See `demo-harness.harness.yml` for comprehensive inline documentation of each
section.

## Part Number Conventions

The examples use realistic part numbers following industry standards:

- **Molex**: 5-digit base PN (e.g., 39012040)
- **Deutsch**: Alphanumeric series codes (e.g., DT04-4P)
- **TE Connectivity**: Numeric series (e.g., 1-1318119-4)
- **Alpha Wire**: Model-gauge-conductor format (e.g., 5304C)

## Color Codes

Wire colors use standard automotive/aerospace abbreviations:

| Code | Color |
|------|-------|
| BK | Black |
| WH | White |
| RD | Red |
| GN | Green |
| BU | Blue |
| YE | Yellow |
| OR | Orange |
| BR | Brown |
| VT | Violet |
| GY | Gray |

Two-tone wires use hyphenated format: `RD-WH` (red with white stripe).

## Notes

- All examples are designed to be valid and buildable
- Part numbers and specifications are realistic but may not reflect current
  availability
- Images referenced in examples should be placed in a local `images/` directory
  or will be resolved via the image scraping pipeline
