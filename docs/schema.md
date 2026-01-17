# Extended YAML Schema Reference

This document describes the complete YAML schema for WireViz Doc harness files. The schema extends WireViz's native format with additional metadata, part specifications, accessories, and manufacturing details.

## Table of Contents

- [File Structure](#file-structure)
- [Metadata Section](#metadata-section)
- [Parts Section](#parts-section)
- [Connectors Section](#connectors-section)
- [Cables Section](#cables-section)
- [Connections Section](#connections-section)
- [Accessories Section](#accessories-section)
- [Complete Example](#complete-example)
- [Validation Rules](#validation-rules)

---

## File Structure

A harness YAML file consists of six main sections:

```yaml
metadata:
  # Document metadata and title block information

parts:
  # Parts library with full specifications

connectors:
  # Connector definitions

cables:
  # Cable definitions with core specifications

connections:
  # Connection matrix (pin-to-pin wiring)

accessories:
  # Additional components (heatshrink, labels, etc.)
```

---

## Metadata Section

Document metadata appears in the title block and manifest.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique harness identifier (e.g., `HAR-0007`) |
| `title` | string | Yes | Document title |
| `revision` | string | Yes | Revision identifier (e.g., `A`, `B`, `1.0`) |
| `date` | string | No | Document date (ISO 8601: `YYYY-MM-DD`) |
| `author` | string | No | Author name |
| `approver` | string | No | Approver name |
| `project` | string | No | Project name or code |
| `custom_fields` | dict | No | Arbitrary key-value pairs |

### Example

```yaml
metadata:
  id: HAR-0007
  title: "Main Power Distribution Harness"
  revision: "B"
  date: "2026-01-17"
  author: "Jane Smith"
  approver: "John Doe"
  project: "PROJECT-X"
  custom_fields:
    department: "Engineering"
    cost_center: "CC-1234"
    drawing_number: "DWG-HAR-0007"
```

---

## Parts Section

The parts library defines reusable part specifications with manufacturer information, alternates, and vendor data.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `primary_pn` | string | No | Primary part number (internal or catalog) |
| `manufacturer` | string | Yes | Manufacturer name |
| `mpn` | string | Yes | Manufacturer part number |
| `description` | string | Yes | Part description |
| `alternates` | list | No | List of alternate parts |
| `fields` | dict | No | Arbitrary vendor fields |
| `image` | object | No | Image specification |

### Alternate Part

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `manufacturer` | string | Yes | Alternate manufacturer |
| `mpn` | string | Yes | Alternate MPN |
| `vendor_sku` | string | No | Vendor SKU |
| `url` | string | No | Product URL |

### Image Specification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `src` | string | Yes | Image file path (relative or absolute) |
| `caption` | string | No | Image caption |
| `height` | string | No | Display height (e.g., `100px`) |

### Part Image Resolution

WireViz Doc resolves part images using a local-first approach. If you prefer not to use automatic web scraping, you can manually place images in your project's `assets/images/` directory.

**Naming Conventions:**

Images are resolved in the following order:

1. **Explicit path** - If `image.src` is specified in the YAML, that path is used directly
2. **Manufacturer + MPN** - `<Manufacturer>_<MPN>.(png|jpg|svg)`
3. **Part Number** - `<PN>.(png|jpg|svg)`

**Examples:**

| Part | Expected Filename |
|------|-------------------|
| Molex 43045-0412 | `Molex_43045-0412.png` |
| PN: CON-001 | `CON-001.png` |
| TE 1-480698-0 | `TE_1-480698-0.png` |

**Directory Structure:**

```
your-project/
├── harnesses/
│   └── main-harness.harness.yml
└── assets/
    └── images/
        ├── Molex_43045-0412.png
        ├── Deutsch_DT04-4P.png
        └── CON-001.png
```

**Tips:**

- Use lowercase or match the exact case in your YAML for consistency
- PNG format is preferred for clean line art; JPG for photographs
- Images are cached locally after first resolution, so web scraping only happens once per part
- In CI mode (`--ci` flag), web scraping is disabled - ensure all images are pre-cached or manually placed

### Example

```yaml
parts:
  MOLEX-430450412:
    primary_pn: "CON-001"
    manufacturer: "Molex"
    mpn: "43045-0412"
    description: "Micro-Fit 3.0 4-position receptacle, vertical"
    alternates:
      - manufacturer: "TE Connectivity"
        mpn: "1-480698-0"
        vendor_sku: "TE-001234"
        url: "https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Customer+Drawing%7F1-480698%7FA%7Fpdf"
    fields:
      lead_time: "4 weeks"
      moq: "100"
      unit_price: "$0.45"
    image:
      src: "parts/Molex_43045-0412.png"
      height: "80px"

  BELDEN-9536:
    manufacturer: "Belden"
    mpn: "9536"
    description: "2-conductor 22 AWG shielded cable, PVC jacket"
    fields:
      color: "Gray"
      temperature_rating: "-20°C to +80°C"
```

---

## Connectors Section

Connectors reference parts from the parts library or define inline specifications.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `part` | string | Conditional | Reference to part ID (required if not inline) |
| `type` | string | No | Connector type (e.g., `Molex`, `D-Sub`) |
| `subtype` | string | No | Connector subtype |
| `pincount` | integer | No | Number of pins |
| `pinlabels` | list | Yes | List of pin labels (1-indexed) |
| `pins` | list | No | Detailed pin definitions |
| `additional_components` | list | No | Accessories (backshells, gaskets) |
| `image` | object | No | Image override |

### Pin Definition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | integer | Yes | Pin number (1-indexed) |
| `label` | string | Yes | Pin label |
| `description` | string | No | Pin description |
| `signal` | string | No | Signal name |

### Example

```yaml
connectors:
  J1:
    part: MOLEX-430450412
    pinlabels: ["+12V", "GND", "CAN_H", "CAN_L"]

  J2:
    part: MOLEX-430450412
    pinlabels: ["+12V", "GND", "CAN_H", "CAN_L"]
    additional_components:
      - type: backshell
        part: MOLEX-430450001
        quantity: 1

  # Inline definition (no part reference)
  J3:
    type: "Molex Micro-Fit 3.0"
    pincount: 6
    pinlabels: ["VCC", "GND", "TX", "RX", "CTS", "RTS"]
    pins:
      - {number: 1, label: "VCC", signal: "POWER_5V"}
      - {number: 2, label: "GND", signal: "GROUND"}
      - {number: 3, label: "TX", signal: "UART_TX"}
      - {number: 4, label: "RX", signal: "UART_RX"}
      - {number: 5, label: "CTS", signal: "UART_CTS"}
      - {number: 6, label: "RTS", signal: "UART_RTS"}
```

---

## Cables Section

Cables define wire specifications, core colors, and twisted pair groupings.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `part` | string | No | Reference to part ID (for catalog cables) |
| `wirecount` | integer | Yes | Number of conductors |
| `cores` | list | Yes | List of core definitions |
| `gauge` | string | Yes | Wire gauge (e.g., `22 AWG`, `0.5 mm²`) |
| `length` | string | Yes | Cable length with unit (e.g., `300 mm`, `1.5 m`) |
| `shield` | string | No | Shield specification (e.g., `overall foil`, `braided`) |
| `notes` | string | No | Cable notes |

### Core Definition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `index` | integer | Yes | Core index (1-based, must match wirecount) |
| `color` | string | Yes | Color specification (see [Color Formats](#color-formats)) |
| `label` | string | No | Core label (e.g., `CAN_H`, `POWER`) |
| `pair_group` | integer | No | Twisted pair group number |
| `twist_spec` | string | No | Twist specification (e.g., `10 twists/ft`) |

### Color Formats

WireViz Doc supports multiple color notation formats:

| Format | Example | Description |
|--------|---------|-------------|
| Single | `RD`, `BK`, `BL` | Standard single color |
| Two-tone | `BL-WH`, `GR-YE` | Base color with stripe |
| 25-pair | `BUWH`, `WHBU` | Telecom 25-pair notation |
| Numbered | `BL1`, `BL2`, `BL3` | Numbered colors |

**Supported color codes:**
`BK` (black), `BN` (brown), `RD` (red), `OG` (orange), `YE` (yellow), `GN` (green), `BL` (blue), `VT` (violet), `GY` (grey), `WH` (white), `PK` (pink), `TQ` (turquoise)

### Example

```yaml
cables:
  W1:
    wirecount: 4
    gauge: "22 AWG"
    length: "500 mm"
    shield: "overall foil with drain"
    cores:
      - {index: 1, color: "WH-GN", label: "CAN_H", pair_group: 1}
      - {index: 2, color: "WH-BN", label: "CAN_L", pair_group: 1}
      - {index: 3, color: "RD", label: "+12V"}
      - {index: 4, color: "BK", label: "GND"}
    notes: "Route away from high-voltage lines"

  W2:
    part: BELDEN-9536
    wirecount: 2
    gauge: "22 AWG"
    length: "300 mm"
    cores:
      - {index: 1, color: "RD"}
      - {index: 2, color: "BK"}
```

---

## Connections Section

The connections section defines the pin-to-pin wiring matrix.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from_connector` | string | Yes | Source connector ID |
| `from_pin` | integer or string | Yes | Source pin (1-indexed or label) |
| `cable` | string | Yes | Cable ID |
| `core` | integer | Yes | Core index (1-indexed) |
| `to_connector` | string | Yes | Destination connector ID |
| `to_pin` | integer or string | Yes | Destination pin (1-indexed or label) |
| `notes` | string | No | Connection notes |

### Example

```yaml
connections:
  # Simple connections
  - {from: J1, from_pin: 1, cable: W1, core: 3, to: J2, to_pin: 1}
  - {from: J1, from_pin: 2, cable: W1, core: 4, to: J2, to_pin: 2}

  # CAN bus twisted pair
  - {from: J1, from_pin: 3, cable: W1, core: 1, to: J2, to_pin: 3, notes: "CAN High"}
  - {from: J1, from_pin: 4, cable: W1, core: 2, to: J2, to_pin: 4, notes: "CAN Low"}

  # Using pin labels instead of numbers
  - {from: J3, from_pin: "VCC", cable: W2, core: 1, to: J4, to_pin: "VCC"}
  - {from: J3, from_pin: "GND", cable: W2, core: 2, to: J4, to_pin: "GND"}
```

---

## Accessories Section

Accessories define additional components like heat shrink, labels, cable ties, and conduit.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Accessory identifier |
| `type` | string | Yes | Accessory type (see below) |
| `part` | string | No | Reference to part ID |
| `quantity` | string | Yes | Quantity with unit (e.g., `30 mm`, `2 pcs`) |
| `location` | string | No | Location specification |
| `notes` | string | No | Additional notes |

### Accessory Types

- `heatshrink` - Heat shrink tubing
- `label` - Cable labels
- `cable_tie` - Cable ties
- `conduit` - Wire conduit/loom
- `tape` - Electrical tape
- `grommet` - Grommets
- `clip` - Cable clips
- `sleeve` - Wire sleeve/expandable braid

### Example

```yaml
accessories:
  HS1:
    type: heatshrink
    part: ALPHA-FIT-221-1/4
    quantity: "30 mm"
    location: "J1 connector exit"
    notes: "3:1 shrink ratio, black"

  LBL1:
    type: label
    quantity: "2 pcs"
    location: "Cable ends"
    notes: "Print 'HAR-0007' on labels"

  CT1:
    type: cable_tie
    part: HELLERMANN-T50R
    quantity: "4 pcs"
    location: "Bundle every 150mm"
```

---

## Complete Example

```yaml
metadata:
  id: HAR-0010
  title: "CAN Bus Harness with Power"
  revision: "A"
  date: "2026-01-17"
  author: "Engineering Team"
  project: "CANBUS-001"

parts:
  MOLEX-430450412:
    manufacturer: "Molex"
    mpn: "43045-0412"
    description: "Micro-Fit 3.0 4-position receptacle"
    image:
      src: "parts/Molex_43045-0412.png"

  ALPHA-FIT-221-1/4:
    manufacturer: "Alpha Wire"
    mpn: "FIT-221-1/4"
    description: "Heat shrink tubing, 3:1, black, 1/4 inch"

connectors:
  J1:
    part: MOLEX-430450412
    pinlabels: ["+12V", "GND", "CAN_H", "CAN_L"]

  J2:
    part: MOLEX-430450412
    pinlabels: ["+12V", "GND", "CAN_H", "CAN_L"]

cables:
  W1:
    wirecount: 4
    gauge: "22 AWG"
    length: "500 mm"
    shield: "overall foil with drain"
    cores:
      - {index: 1, color: "RD", label: "+12V"}
      - {index: 2, color: "BK", label: "GND"}
      - {index: 3, color: "WH-GN", label: "CAN_H", pair_group: 1}
      - {index: 4, color: "WH-BN", label: "CAN_L", pair_group: 1}

connections:
  - {from: J1, from_pin: 1, cable: W1, core: 1, to: J2, to_pin: 1}
  - {from: J1, from_pin: 2, cable: W1, core: 2, to: J2, to_pin: 2}
  - {from: J1, from_pin: 3, cable: W1, core: 3, to: J2, to_pin: 3}
  - {from: J1, from_pin: 4, cable: W1, core: 4, to: J2, to_pin: 4}

accessories:
  HS1:
    type: heatshrink
    part: ALPHA-FIT-221-1/4
    quantity: "30 mm"
    location: "J1 exit"

  HS2:
    type: heatshrink
    part: ALPHA-FIT-221-1/4
    quantity: "30 mm"
    location: "J2 exit"
```

---

## Validation Rules

WireViz Doc validates harness files against these rules:

### Schema Validation

- All required fields must be present
- Field types must match schema (string, integer, list, dict)
- Enum fields must use allowed values

### Reference Validation

- All part references must exist in `parts` section
- All connector references in connections must exist in `connectors` section
- All cable references in connections must exist in `cables` section

### Connection Validation

- Pin numbers must be valid for the referenced connector
- Core indices must be valid for the referenced cable (1 to wirecount)
- No duplicate connections (same pin used twice)

### Color Validation

- Color codes must be from the supported set
- Two-tone colors must follow `BASE-STRIPE` format
- 25-pair colors must follow telecom standards

### Part Number Validation

- Part numbers should follow expected patterns (warnings only)
- Manufacturer and MPN should be non-empty

### Image Validation

- Image paths should exist (warning if missing)
- Image formats should be PNG or JPG

---

## Tips and Best Practices

### Part Library Organization

Create reusable part definitions in a separate file and use YAML anchors:

```yaml
# parts-library.yml
part_templates:
  molex_microfit_4pos: &molex_4pos
    manufacturer: "Molex"
    type: "Micro-Fit 3.0"
    pincount: 4

# harness.yml
connectors:
  J1:
    <<: *molex_4pos
    mpn: "43045-0412"
    pinlabels: ["+12V", "GND", "SIG1", "SIG2"]
```

### Color Naming

Use consistent color naming throughout your organization:
- Define a standard color palette in your documentation
- Use labels for signal identification, colors for physical wire identification
- Consider color-blind friendly color schemes for critical signals

### Twisted Pairs

Always specify twisted pairs using `pair_group`:
- Differential signals (CAN, RS-485, USB) should be paired
- Document twist specifications when critical (e.g., "10 twists per foot")
- Use shield specification for overall shield or per-pair shield

### Accessories

Include all manufacturing details:
- Heat shrink length and location
- Label text and placement
- Cable tie spacing requirements
- Any special assembly notes

### Revision Control

Use semantic versioning for revisions:
- Letters for minor changes (A, B, C)
- Numbers for major revisions (1.0, 2.0)
- Update date and revision together
- Document changes in comments or separate changelog
