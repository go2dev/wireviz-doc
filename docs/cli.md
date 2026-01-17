# CLI Reference

Complete command-line interface documentation for WireViz Doc.

## Table of Contents

- [Installation](#installation)
- [Global Options](#global-options)
- [Commands](#commands)
  - [build](#wvdoc-build)
  - [lint](#wvdoc-lint)
  - [images](#wvdoc-images)
- [Exit Codes](#exit-codes)
- [Configuration](#configuration)
- [Examples](#examples)

---

## Installation

Before using WireViz Doc, ensure system dependencies are installed:

```bash
# Verify Graphviz installation
dot -V

# Should output: dot - graphviz version X.X.X
```

Install WireViz Doc:

```bash
# Using uv (recommended)
uv pip install wireviz-doc

# Using pip
pip install wireviz-doc

# Verify installation
wvdoc --version
```

---

## Global Options

These options apply to all commands:

### `--verbose` / `-v`

Enable detailed output including debug information.

```bash
wvdoc build harness.yml --verbose
```

**Output includes:**
- File paths being processed
- Validation steps
- Image resolution details
- WireViz execution output
- SVG composition steps

### `--quiet` / `-q`

Suppress all output except errors.

```bash
wvdoc build harness.yml --quiet
```

**Use cases:**
- CI/CD pipelines where you only care about failures
- Batch processing multiple files
- Scripted builds

### `--config <path>`

Specify custom configuration file path.

```bash
wvdoc build harness.yml --config ./my-config.yml
```

**Default locations searched (in order):**
1. `./.wireviz-doc.yml`
2. `~/.config/wireviz-doc/config.yml`
3. Built-in defaults

### `--version`

Display version information and exit.

```bash
wvdoc --version
# Output: WireViz Doc 1.0.0
```

### `--help` / `-h`

Show help message and exit.

```bash
wvdoc --help              # General help
wvdoc build --help        # Command-specific help
```

---

## Commands

## `wvdoc build`

Generate complete wiring documentation from harness YAML file(s).

### Synopsis

```bash
wvdoc build [OPTIONS] <file-or-glob>
```

### Arguments

**`<file-or-glob>`** (required)

Single file path or glob pattern for harness YAML files.

```bash
# Single file
wvdoc build harness.yml

# Glob pattern (quote to prevent shell expansion)
wvdoc build "harnesses/**/*.harness.yml"
wvdoc build "*.harness.yml"
```

### Options

#### `--output-dir <path>` / `-o <path>`

Output directory for generated files.

**Default:** `./build`

```bash
wvdoc build harness.yml --output-dir dist
wvdoc build harness.yml -o output/docs
```

**Directory structure:**
```
<output-dir>/
└── <harness-id>/
    ├── diagram.svg
    ├── diagram.pdf
    ├── wireviz.yml
    ├── bom.tsv
    ├── wiring_table.tsv
    └── manifest.json
```

#### `--format <format>` / `-f <format>`

Output format selection.

**Options:** `svg`, `pdf`, `all` (default: `all`)

```bash
wvdoc build harness.yml --format svg      # SVG only
wvdoc build harness.yml --format pdf      # PDF only
wvdoc build harness.yml --format all      # Both (default)
```

**Generated files by format:**

| Format | Files Generated |
|--------|----------------|
| `svg` | `diagram.svg`, `bom.tsv`, `wiring_table.tsv`, `wireviz.yml` |
| `pdf` | `diagram.pdf`, `bom.tsv`, `wiring_table.tsv`, `wireviz.yml` |
| `all` | All of the above |

#### `--allow-missing-images`

Continue build even if part images are missing.

```bash
wvdoc build harness.yml --allow-missing-images
```

**Behavior:**
- Missing images show placeholder or are omitted
- Warning logged but build succeeds
- Useful during early development

**Without flag:**
- Missing images cause build failure (exit code 1)
- Forces image resolution before committing

#### `--no-cache`

Disable image cache and force re-resolution.

```bash
wvdoc build harness.yml --no-cache
```

**Use cases:**
- Image files updated
- Cache corruption
- Testing image resolution

### Examples

**Basic build:**
```bash
wvdoc build my-harness.harness.yml
```

**Build all harnesses in directory:**
```bash
wvdoc build "harnesses/**/*.harness.yml"
```

**PDF only to custom directory:**
```bash
wvdoc build harness.yml --format pdf --output-dir production/docs
```

**Verbose build with missing images allowed:**
```bash
wvdoc build harness.yml --verbose --allow-missing-images
```

---

## `wvdoc lint`

Validate harness YAML against schema and check for errors.

### Synopsis

```bash
wvdoc lint [OPTIONS] <file>
```

### Arguments

**`<file>`** (required)

Path to harness YAML file to validate.

```bash
wvdoc lint harness.yml
```

### Options

#### `--strict`

Treat warnings as errors.

```bash
wvdoc lint harness.yml --strict
```

**Warning → Error examples:**
- Missing part images
- Unusual part number formats
- Color names not in standard set
- Missing optional fields (author, approver)

**Use cases:**
- Pre-commit hooks requiring perfect validation
- Final validation before release
- Enforcing team standards

#### `--fix`

Automatically fix issues where possible.

```bash
wvdoc lint harness.yml --fix
```

**Auto-fixable issues:**
- Normalize color names (`red` → `RD`)
- Add missing required fields with defaults
- Sort sections alphabetically
- Format whitespace

**Not auto-fixable:**
- Invalid references
- Connection errors
- Schema violations

### Validation Checks

**Schema validation:**
- Required fields present
- Correct field types
- Valid enum values

**Reference validation:**
- Part references exist
- Connector/cable references valid
- Pin/core indices in range

**Connection validation:**
- Valid pin assignments
- No duplicate connections
- Proper core mapping

**Color validation:**
- Supported color codes
- Proper two-tone format
- 25-pair compliance

**Part validation:**
- Part numbers follow patterns (warning)
- Manufacturer and MPN non-empty
- Image paths exist (warning)

### Output

**Success:**
```bash
$ wvdoc lint harness.yml
✓ Schema validation passed
✓ Reference validation passed
✓ Connection validation passed
✓ Color validation passed
✓ harness.yml is valid
```

**Errors:**
```bash
$ wvdoc lint harness.yml
✗ Schema validation failed:
  - metadata.id: field required
  - connectors.J1.part: part 'INVALID-PART' not found in parts library

✗ Connection validation failed:
  - Connection 0: pin J1:5 exceeds pincount (4)

✗ harness.yml validation failed with 3 errors
```

**Warnings (with `--strict`):**
```bash
$ wvdoc lint harness.yml --strict
⚠ Warnings (--strict mode):
  - parts.MOLEX-001: missing image
  - metadata.author: field recommended but missing

✗ harness.yml validation failed with 2 warnings (strict mode)
```

### Examples

**Basic validation:**
```bash
wvdoc lint harness.yml
```

**Strict validation for CI:**
```bash
wvdoc lint harness.yml --strict
```

**Fix and re-validate:**
```bash
wvdoc lint harness.yml --fix
wvdoc lint harness.yml
```

---

## `wvdoc images`

Resolve and download part images.

### Synopsis

```bash
wvdoc images [OPTIONS] <file>
```

### Arguments

**`<file>`** (required)

Path to harness YAML file.

```bash
wvdoc images harness.yml
```

### Options

#### `--scrape`

Enable web scraping for missing images.

**Default:** Disabled (local resolution only)

```bash
wvdoc images harness.yml --scrape
```

**Image resolution order:**
1. Explicit image path in YAML
2. Local cache: `images/<manufacturer>_<mpn>.(png|jpg)`
3. Local cache: `images/<part-id>.(png|jpg)`
4. **If `--scrape`:** Scrape from vendor sources
5. Placeholder or fail

**Scraped images:**
- Saved to local cache
- Provenance recorded in `manifest.json`
- Reused in future builds

#### `--ci`

CI mode - forbid scraping, fail on missing images.

```bash
wvdoc images harness.yml --ci
```

**Behavior:**
- Scraping disabled (even if `--scrape` also specified)
- Missing images cause failure
- Ensures deterministic builds
- Forces image commitment to repository

**Use case:**
- CI/CD pipelines
- Reproducible builds
- Preventing network dependencies in automation

#### `--update`

Update existing cached images.

```bash
wvdoc images harness.yml --update
```

**Behavior:**
- Re-download cached images
- Update provenance metadata
- Useful when vendor images updated

#### `--cache-dir <path>`

Custom image cache directory.

**Default:** `./images`

```bash
wvdoc images harness.yml --cache-dir /shared/part-images
```

### Image Resolution Process

1. **Explicit path:** Check YAML `image.src`
2. **Manufacturer pattern:** `<cache-dir>/<manufacturer>_<mpn>.png`
3. **Part ID pattern:** `<cache-dir>/<part-id>.png`
4. **Web scraping (if enabled):**
   - Vendor-specific scrapers
   - Common parts databases
   - Manufacturer websites
5. **Fallback:** Placeholder or error

### Manifest

Image metadata is stored in `manifest.json`:

```json
{
  "images": {
    "MOLEX-430450412": {
      "source": "local",
      "path": "images/Molex_43045-0412.png",
      "timestamp": "2026-01-17T10:30:00Z"
    },
    "BELDEN-9536": {
      "source": "scraped",
      "url": "https://www.belden.com/...",
      "path": "images/Belden_9536.jpg",
      "timestamp": "2026-01-17T10:31:00Z",
      "sha256": "a3d5e..."
    }
  }
}
```

### Examples

**Resolve local images only:**
```bash
wvdoc images harness.yml
```

**Download missing images from web:**
```bash
wvdoc images harness.yml --scrape
```

**CI validation (no scraping):**
```bash
wvdoc images harness.yml --ci
```

**Update all cached images:**
```bash
wvdoc images harness.yml --scrape --update
```

---

## Exit Codes

WireViz Doc uses standard exit codes:

| Code | Meaning | Examples |
|------|---------|----------|
| `0` | Success | Validation passed, build completed |
| `1` | Error | Schema validation failed, missing dependencies, file not found |
| `2` | Warning | Completed with warnings (missing images with `--allow-missing-images`) |

### Usage in Scripts

**Bash:**
```bash
#!/bin/bash
wvdoc build harness.yml
if [ $? -eq 0 ]; then
    echo "Build succeeded"
else
    echo "Build failed"
    exit 1
fi
```

**CI/CD (GitHub Actions):**
```yaml
- name: Build documentation
  run: wvdoc build "harnesses/**/*.harness.yml"
  # Fails workflow on non-zero exit code
```

**Pre-commit hook:**
```bash
#!/bin/bash
wvdoc lint "$@" --strict
exit $?
```

---

## Configuration

Configuration file format (`.wireviz-doc.yml`):

```yaml
# Output settings
output:
  directory: "build"
  formats: ["svg", "pdf"]
  allow_missing_images: false

# Image settings
images:
  cache_directory: "images"
  scraping_enabled: false
  vendor_scrapers:
    - digikey
    - mouser
    - molex

# Validation settings
validation:
  strict: false
  allowed_colors:
    - BK
    - BN
    - RD
    - OG
    - YE
    - GN
    - BL
    - VT
    - GY
    - WH
    - PK
    - TQ

# Template settings
templates:
  title_block: "templates/title-block.svg.j2"
  sheet: "templates/sheet-a4.svg.j2"

# WireViz settings
wireviz:
  background_color: "white"
  font_name: "sans-serif"
  mini_bom_mode: true
```

### Environment Variables

Override configuration with environment variables:

```bash
export WVDOC_OUTPUT_DIR="dist"
export WVDOC_IMAGES_CACHE="~/.cache/wireviz-doc/images"
export WVDOC_STRICT_MODE="true"

wvdoc build harness.yml
```

**Variable format:** `WVDOC_<SECTION>_<KEY>` (uppercase, underscores)

---

## Examples

### Development Workflow

```bash
# Initial validation
wvdoc lint harness.yml

# Fix issues
wvdoc lint harness.yml --fix

# Resolve images
wvdoc images harness.yml --scrape

# Build documentation
wvdoc build harness.yml --verbose

# Review output
open build/HAR-0001/diagram.pdf
```

### Production Build

```bash
# Strict validation
wvdoc lint harness.yml --strict

# CI-mode image check
wvdoc images harness.yml --ci

# Build PDF for manufacturing
wvdoc build harness.yml --format pdf --output-dir production
```

### Batch Processing

```bash
# Build all harnesses
for file in harnesses/*.harness.yml; do
    echo "Building $file..."
    wvdoc build "$file" --quiet
done

# Or using glob
wvdoc build "harnesses/**/*.harness.yml" --quiet
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Get staged .harness.yml files
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.harness\.yml$')

if [ -n "$FILES" ]; then
    echo "Validating harness files..."
    for file in $FILES; do
        wvdoc lint "$file" --strict || exit 1
    done

    echo "Building documentation..."
    wvdoc build $FILES --ci || exit 1

    # Stage generated outputs
    git add build/
fi
```

### CI/CD Integration

```bash
# GitHub Actions workflow step
- name: Validate and build harnesses
  run: |
    wvdoc lint harnesses/*.harness.yml --strict
    wvdoc images harnesses/*.harness.yml --ci
    wvdoc build harnesses/*.harness.yml --output-dir artifacts

- name: Upload artifacts
  uses: actions/upload-artifact@v3
  with:
    name: wiring-documentation
    path: artifacts/
```

---

## Troubleshooting

### Common Issues

**"Graphviz not found"**
```bash
# Install Graphviz
brew install graphviz  # macOS
sudo apt install graphviz  # Ubuntu

# Verify
dot -V
```

**"Part reference not found"**
- Check part ID exists in `parts` section
- Verify spelling matches exactly (case-sensitive)
- Use `wvdoc lint` to identify all reference errors

**"Image not found"**
- Verify image path in YAML or cache directory
- Use `wvdoc images --scrape` to download
- Use `--allow-missing-images` to proceed without images

**"Invalid color specification"**
- Check supported color codes
- Use standard two-tone format: `BASE-STRIPE`
- Run `wvdoc lint` for color validation

**"Connection validation failed"**
- Verify pin numbers within connector pincount
- Verify core indices within cable wirecount
- Check for duplicate pin assignments

---

## See Also

- [Schema Reference](schema.md) - Complete YAML schema documentation
- [CI/CD Integration](integration.md) - GitHub Actions, pre-commit hooks
- [WireViz Documentation](https://github.com/formatc1702/WireViz) - Underlying diagram engine
