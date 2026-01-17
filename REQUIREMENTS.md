# WireViz Drawing Generator — Requirements Specification

## Overview

A local-first, CI-ready documentation pipeline that converts extended harness YAML files into factory-shareable wiring documentation. Uses WireViz and Graphviz for diagram generation with a Python wrapper adding title blocks, wiring schedules, enhanced BOM content, part images, and machine-readable exports.

---

## 1. Project Infrastructure

### 1.1 Repository Setup
- [ ] Initialize git repository
- [ ] Configure `.gitignore` (Python, macOS, IDE, `.claude/`)
- [ ] Create GitHub repository under `go2dev` account
- [ ] Enable conventional commits for semantic versioning

### 1.2 Python Project Configuration
- [ ] Target Python 3.9+ for broad compatibility
- [ ] Use `uv` for package management
- [ ] Use `ruff` for linting and formatting
- [ ] Use `ty` for type checking
- [ ] Provide `pip install` fallback for users without uv
- [ ] Runtime check for system dependencies (Graphviz `dot` binary)

### 1.3 Dependencies
| Package | Purpose |
|---------|---------|
| `pyyaml` | YAML parsing |
| `pydantic` | Data validation and models |
| `jinja2` | SVG/HTML templating |
| `lxml` | XML/SVG manipulation |
| `httpx` | HTTP client (modern requests alternative) |
| `beautifulsoup4` | HTML parsing for image scraping |
| `cairosvg` | SVG to PDF conversion |
| `wireviz` | Diagram generation engine |
| `typer` | CLI framework |

**System Dependencies:**
| Binary | Purpose |
|--------|---------|
| `graphviz` (`dot`) | Graph rendering |

---

## 2. CLI Interface

### 2.1 Command Structure
```
wvdoc <command> [options] <args>
```

### 2.2 Commands

#### `wvdoc build <file-or-glob>`
- [ ] Accept single file or glob pattern
- [ ] Generate all outputs (diagram, BOM, wiring table, PDF)
- [ ] Support `--output-dir` option
- [ ] Support `--format` option (svg, pdf, all)
- [ ] Exit codes: 0=success, 1=error, 2=warnings
- [ ] Suitable for commit hooks and CI

#### `wvdoc images <file>`
- [ ] Resolve and download images only
- [ ] Update local cache
- [ ] Record provenance in manifest
- [ ] Support `--scrape` flag (off by default)
- [ ] Support `--ci` flag (forbids scraping)

#### `wvdoc lint <file>`
- [ ] Validate extended YAML schema
- [ ] Check for missing part numbers
- [ ] Validate wire colors against known set
- [ ] Flag missing images
- [ ] Report connection validity errors
- [ ] Support `--strict` mode

### 2.3 Global Options
- [ ] `--verbose` / `-v` for detailed output
- [ ] `--quiet` / `-q` for minimal output
- [ ] `--config` for custom config file path
- [ ] `--version` to display version

---

## 3. Data Model

### 3.1 Internal Entities (Pydantic Models)

#### `DocumentMeta`
- [ ] `id`: Harness identifier (e.g., `HAR-0007`)
- [ ] `title`: Document title
- [ ] `revision`: Revision string
- [ ] `date`: Document date
- [ ] `author`: Author name
- [ ] `approver`: Approver name (optional)
- [ ] `project`: Project name (optional)
- [ ] `custom_fields`: Dict for arbitrary metadata

#### `Part`
- [ ] `id`: Internal reference ID
- [ ] `primary_pn`: Primary part number
- [ ] `manufacturer`: Manufacturer name
- [ ] `mpn`: Manufacturer part number
- [ ] `description`: Part description
- [ ] `alternates`: List of alternate parts
- [ ] `fields`: Dict for arbitrary vendor fields
- [ ] `image`: Image specification (optional)

#### `Connector` (extends Part)
- [ ] `type`: Connector type
- [ ] `subtype`: Connector subtype
- [ ] `pincount`: Number of pins
- [ ] `pinlabels`: List of pin labels
- [ ] `pins`: Detailed pin definitions
- [ ] `additional_components`: List of accessories

#### `Cable` (extends Part)
- [ ] `wirecount`: Number of conductors
- [ ] `cores`: List of Core definitions
- [ ] `gauge`: Wire gauge (AWG or mm²)
- [ ] `length`: Cable length with unit
- [ ] `shield`: Shield specification (optional)
- [ ] `notes`: Cable notes

#### `Core`
- [ ] `index`: Core index (1-based)
- [ ] `color`: Color specification
- [ ] `label`: Core label (e.g., "CAN_H")
- [ ] `pair_group`: Twisted pair group (optional)
- [ ] `twist_spec`: Twist specification (optional)

#### `Accessory`
- [ ] `type`: Accessory type (heatshrink, label, conduit, etc.)
- [ ] `part`: Part reference
- [ ] `quantity`: Quantity with unit
- [ ] `location`: Location specification (optional)

#### `Connection`
- [ ] `from_connector`: Source connector ID
- [ ] `from_pin`: Source pin
- [ ] `cable`: Cable ID
- [ ] `core`: Core index
- [ ] `to_connector`: Destination connector ID
- [ ] `to_pin`: Destination pin
- [ ] `notes`: Connection notes (optional)

### 3.2 Alternate Part
- [ ] `manufacturer`: Alternate manufacturer
- [ ] `mpn`: Alternate MPN
- [ ] `vendor_sku`: Vendor SKU (optional)
- [ ] `url`: Product URL (optional)

### 3.3 Image Specification
- [ ] `src`: Image source path
- [ ] `caption`: Image caption (optional)
- [ ] `height`: Display height (optional)

---

## 4. Extended YAML Schema

### 4.1 Schema Structure
```yaml
metadata:
  id: HAR-0007
  title: "Main Power Harness"
  revision: "A"
  # ... other DocumentMeta fields

parts:
  # Parts library with full specifications

connectors:
  # Connector definitions (reference parts or inline)

cables:
  # Cable definitions with core specifications

connections:
  # Connection matrix

accessories:
  # Heatshrink, labels, etc.
```

### 4.2 Validation Rules
- [ ] Every referenced connector/cable/accessory must exist
- [ ] Every connection must reference valid pins/cores
- [ ] Twisted pair definitions must reference existing cores
- [ ] Color tokens normalized to canonical format
- [ ] Part numbers validated against expected patterns

---

## 5. Processing Pipeline

### 5.1 Extended YAML Parsing
- [ ] Load and parse extended YAML
- [ ] Validate against schema
- [ ] Normalize color tokens
- [ ] Resolve part references
- [ ] Build internal model

### 5.2 Image Resolution
- [ ] Check explicit image override in YAML
- [ ] Try local path: `<manufacturer>_<mpn>.(png|jpg)`
- [ ] Try local path: `<pn>.(png|jpg)`
- [ ] Optional: scrape from vendor sources
- [ ] Cache downloaded images with provenance
- [ ] Record in manifest.json

### 5.3 WireViz YAML Generation
- [ ] Generate canonical WireViz YAML from internal model
- [ ] Include only WireViz-supported keys
- [ ] Inject resolved image paths
- [ ] Support YAML anchors for templates
- [ ] Output to `build/<id>/wireviz.yml`

### 5.4 WireViz Execution
- [ ] Run WireViz on generated YAML
- [ ] Capture `.gv`, `.svg`, `.bom.tsv` outputs
- [ ] Handle WireViz errors gracefully

### 5.5 Wiring Table Generation
- [ ] Generate from internal connection model
- [ ] Columns:
  - From Connector (refdes)
  - From Pin
  - To Connector (refdes)
  - To Pin
  - Cable Ref
  - Core Index
  - Core Label
  - Color (display format)
  - Pair Group
  - Twist Spec
  - Shield/Drain
  - Notes
- [ ] Output as TSV/CSV
- [ ] Generate HTML/SVG for embedding

### 5.6 BOM Augmentation
- [ ] Include accessories (heatshrink, labels, etc.)
- [ ] Include process components (crimps, seals)
- [ ] Add alternates information
- [ ] Include arbitrary vendor fields
- [ ] Output augmented BOM as TSV

### 5.7 Final Document Composition
- [ ] Use SVG template (`sheet.svg.j2`)
- [ ] Embed WireViz diagram
- [ ] Render title block with metadata
- [ ] Render BOM table
- [ ] Render wiring table
- [ ] Handle large tables (pagination or summary)
- [ ] Convert to PDF via CairoSVG

---

## 6. Color Handling

### 6.1 Input Formats Supported
- [ ] Two-tone: `BL-WH`, `GR-YE`
- [ ] 25-pair: `BUWH`, `WHBU`
- [ ] Numbered: `BL1`, `BL2`, `BL3`
- [ ] Standard single: `BL`, `WH`, `GR`

### 6.2 Normalization
- [ ] Parse to: `display_color`, `base_color`, `stripe_color`
- [ ] Wiring table uses `display_color`
- [ ] WireViz uses `base_color`
- [ ] Validate against known color set

---

## 7. Heatshrink and Accessories

### 7.1 BOM Integration (Layer 1)
- [ ] Convert to `additional_components` in WireViz YAML
- [ ] Include type, quantity, unit, part number
- [ ] Appear in BOM output

### 7.2 Visual Annotation (Layer 2)
- [ ] Add `xlabel` to Graphviz edges
- [ ] Format: `"HS1 30mm"` or similar
- [ ] Optional SVG overlay for precise positioning

---

## 8. Output Artifacts

### 8.1 Per-Harness Outputs
| File | Description |
|------|-------------|
| `diagram.svg` | Final factory-ready SVG with title block, BOM, wiring table |
| `diagram.pdf` | PDF version of above |
| `wireviz.yml` | Generated WireViz-compatible YAML |
| `bom.tsv` | BOM export for procurement/manufacturing |
| `wiring_table.tsv` | Wiring schedule for assembly/QA |
| `manifest.json` | Provenance and hashes (optional) |

### 8.2 Output Directory Structure
```
build/
└── HAR-0007/
    ├── diagram.svg
    ├── diagram.pdf
    ├── wireviz.yml
    ├── wireviz.gv
    ├── bom.tsv
    ├── wiring_table.tsv
    └── manifest.json
```

---

## 9. CI/CD Integration

### 9.1 Local Pre-commit Hook
- [ ] Document hook configuration for user repos
- [ ] Trigger on `harnesses/**/*.harness.yml`
- [ ] Run `wvdoc build {files}`
- [ ] Fail on schema errors
- [ ] Fail on missing images (unless `--allow-missing-images`)
- [ ] Fail if scraping attempted without permission

### 9.2 GitHub Actions Workflow
- [ ] Provide example workflow YAML
- [ ] Install system dependencies (Graphviz)
- [ ] Install Python dependencies
- [ ] Run build in CI mode (no scraping)
- [ ] Upload artifacts

---

## 10. Documentation

### 10.1 README
- [ ] Project overview and purpose
- [ ] Installation instructions (uv and pip)
- [ ] Quick start guide
- [ ] CLI reference
- [ ] Link to full documentation

### 10.2 Extended Documentation
- [ ] YAML schema reference
- [ ] Data model documentation
- [ ] Configuration options
- [ ] CI/CD integration guide
- [ ] Contributing guidelines

### 10.3 Examples
- [ ] Demo harness YAML (`examples/demo-harness.harness.yml`)
- [ ] Parts library example
- [ ] SVG template (`examples/templates/sheet-a4.svg.j2`)
- [ ] Expected outputs for comparison

---

## 11. Risk Mitigations

### 11.1 Scraping Fragility
- [ ] Vendor-specific scrapers (modular)
- [ ] Aggressive caching with TTL
- [ ] Opt-in only (off by default)
- [ ] CI mode forbids scraping
- [ ] Graceful degradation (missing image placeholder)

### 11.2 Graphviz Rendering Quirks
- [ ] Use SVG composition (not GV table patching)
- [ ] Keep tables separate from diagram
- [ ] Test with various table sizes
- [ ] Document known limitations

### 11.3 Large Wiring Tables
- [ ] Pagination support in PDF output
- [ ] Summary table in diagram, full table external
- [ ] Configurable row limits

---

## 12. Future Considerations (Out of Scope)

These items are noted for future development but not part of initial release:

- Multi-page harness documentation
- Interactive HTML output
- Database backend for parts library
- Web UI for harness editing
- Diff/changelog between harness revisions
- Integration with ERP/PLM systems

---

## Revision History

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0 | 2026-01-17 | Initial requirements specification |
