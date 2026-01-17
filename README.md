# WireViz Doc

**Generate factory-ready wiring documentation from YAML**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://img.shields.io/badge/CI-passing-brightgreen.svg)](#)

---

## Overview

WireViz Doc is a local-first, CI-ready documentation pipeline that converts extended harness YAML files into factory-shareable wiring documentation. It leverages [WireViz](https://github.com/formatc1702/WireViz) and Graphviz for diagram generation, adding professional title blocks, comprehensive wiring schedules, enhanced BOMs with alternates, part images, and machine-readable exports.

**Why WireViz Doc?**

- **Complete Documentation**: Beyond simple diagrams, generate full assembly documentation with wiring tables, BOMs, and part images
- **Deterministic Output**: Same input always produces same output - perfect for version control and CI/CD
- **Factory-Ready**: Professional title blocks, revision tracking, and formats ready for manufacturing
- **Local-First**: Works offline, no cloud dependencies, all data stays on your machine
- **Extensible**: Rich YAML schema supports complex harness specifications with accessories, alternates, and metadata

## Key Features

- **Extended YAML schema** for complete harness documentation beyond WireViz's native format
- **WireViz-powered diagram generation** with automatic layout and routing
- **Automatic wiring table generation** with pin-to-pin connections, colors, and pairs
- **BOM with alternates and vendor fields** for procurement and manufacturing
- **Part image resolution** (local-first) with optional web scraping
- **Factory-ready PDF/SVG output** with professional title blocks and revision control
- **CI/CD ready** with deterministic builds, linting, and pre-commit hooks
- **Comprehensive validation** of schemas, connections, and part references

## Quick Start

### System Requirements

- Python 3.9 or higher
- [Graphviz](https://graphviz.org/download/) (required for diagram rendering)

**Install Graphviz:**

```bash
# macOS
brew install graphviz

# Ubuntu/Debian
sudo apt-get install graphviz

# Windows (using Chocolatey)
choco install graphviz
```

### Installation

**Using uv (recommended):**

```bash
uv pip install wireviz-doc
```

**Using pip:**

```bash
pip install wireviz-doc
```

**From source:**

```bash
git clone https://github.com/go2dev/wireviz-doc.git
cd wireviz-doc
uv pip install -e .
# or: pip install -e .
```

### Basic Usage

Create a harness YAML file (e.g., `my-harness.harness.yml`):

```yaml
metadata:
  id: HAR-0001
  title: "Power Distribution Harness"
  revision: "A"
  date: "2026-01-17"
  author: "Engineering Team"

parts:
  MOLEX-430450412:
    manufacturer: Molex
    mpn: 43045-0412
    description: "Micro-Fit 3.0 4-position receptacle"

connectors:
  J1:
    part: MOLEX-430450412
    pinlabels: [VCC, GND, SIG, NC]

cables:
  W1:
    wirecount: 2
    gauge: 22 AWG
    length: 300 mm
    cores:
      - {index: 1, color: RD, label: VCC}
      - {index: 2, color: BK, label: GND}

connections:
  - {from: J1, from_pin: 1, cable: W1, core: 1, to: J2, to_pin: 1}
  - {from: J1, from_pin: 2, cable: W1, core: 2, to: J2, to_pin: 2}
```

Generate documentation:

```bash
wvdoc build my-harness.harness.yml
```

This creates:
- `build/HAR-0001/diagram.svg` - Complete wiring diagram with title block
- `build/HAR-0001/diagram.pdf` - PDF version
- `build/HAR-0001/bom.tsv` - Bill of materials
- `build/HAR-0001/wiring_table.tsv` - Pin-to-pin wiring schedule
- `build/HAR-0001/wireviz.yml` - Generated WireViz YAML

## CLI Reference

### Commands

**`wvdoc build <file-or-glob>`**

Generate complete documentation from harness YAML file(s).

```bash
wvdoc build harness.yml                    # Single file
wvdoc build "harnesses/**/*.harness.yml"   # Glob pattern
wvdoc build harness.yml --format pdf       # PDF only
wvdoc build harness.yml --output-dir dist  # Custom output directory
```

**`wvdoc lint <file>`**

Validate harness YAML against schema and check for errors.

```bash
wvdoc lint harness.yml           # Standard validation
wvdoc lint harness.yml --strict  # Strict mode (warnings as errors)
```

**`wvdoc images <file>`**

Resolve and download part images.

```bash
wvdoc images harness.yml           # Resolve local images
wvdoc images harness.yml --scrape  # Enable web scraping
wvdoc images harness.yml --ci      # CI mode (no scraping allowed)
```

### Global Options

- `--verbose` / `-v` - Detailed output
- `--quiet` / `-q` - Minimal output
- `--config <path>` - Custom config file
- `--version` - Show version

**Exit Codes:**
- `0` - Success
- `1` - Error (validation failure, missing dependencies)
- `2` - Warning (completed with warnings)

See [docs/cli.md](docs/cli.md) for complete CLI documentation.

## Example Output

The `wvdoc build` command generates a complete documentation package:

```
build/HAR-0001/
├── diagram.svg          # Factory-ready diagram with title block, BOM, and wiring table
├── diagram.pdf          # PDF version for printing/distribution
├── wireviz.yml          # Generated WireViz YAML (for reference)
├── wireviz.gv           # Graphviz source (intermediate)
├── bom.tsv              # Bill of materials (TSV for spreadsheets)
├── wiring_table.tsv     # Wiring schedule (TSV for assembly)
└── manifest.json        # Build metadata and provenance
```

The final `diagram.svg`/`diagram.pdf` includes:
- Professional title block with revision, date, author
- Wiring diagram with connectors, cables, and connections
- Bill of materials table with part numbers, descriptions, quantities
- Wiring schedule with pin-to-pin connections and wire colors
- Part images (when available)

## Part Images

WireViz Doc resolves part images using a local-first approach. You can either let the tool scrape images from vendor websites (opt-in) or manually place images in your project.

**Manual Image Placement:**

Place images in `assets/images/` using these naming conventions:

| Pattern | Example |
|---------|---------|
| `<Manufacturer>_<MPN>.(png\|jpg)` | `Molex_43045-0412.png` |
| `<PartNumber>.(png\|jpg)` | `CON-001.png` |

```
your-project/
└── assets/
    └── images/
        ├── Molex_43045-0412.png
        ├── Deutsch_DT04-4P.png
        └── TE_1-480698-0.jpg
```

This is the recommended approach for CI/CD pipelines where deterministic builds are required. See [docs/schema.md](docs/schema.md#part-image-resolution) for complete details.

## Examples

Browse the [examples/](examples/) directory for complete working examples:

- **Basic harness** - Simple point-to-point wiring
- **Complex harness** - Multi-cable, twisted pairs, shielding
- **Parts library** - Reusable part definitions
- **Accessories** - Heat shrink, labels, cable management

## Documentation

- [Schema Reference](docs/schema.md) - Complete YAML schema documentation
- [CLI Reference](docs/cli.md) - Detailed command-line interface guide
- [CI/CD Integration](docs/integration.md) - GitHub Actions, pre-commit hooks
- [Custom Templates Tutorial](docs/tutorial-custom-templates.md) - Design branded output templates
- [Template Design Guide](docs/template-design.md) - Advanced template customization

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run linting and tests (`ruff check .` and `pytest`)
5. Commit with conventional commits (`feat:`, `fix:`, `docs:`)
6. Push to your fork and submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [WireViz](https://github.com/formatc1702/WireViz) by @formatc1702 - The excellent diagram generation engine that powers this tool
- [Graphviz](https://graphviz.org/) - Graph visualization library
- The open-source community for inspiration and tools

## Authors

Created by **[Go2Dev](https://github.com/go2dev)** / **[Whatever Together](https://whatevertogether.net)**

---

**Need Help?** Open an [issue](https://github.com/go2dev/wireviz-doc/issues) or check the [documentation](docs/).
