# Designing Output Templates with Inkscape/Illustrator

This guide explains how to create custom SVG templates using graphical design tools that work seamlessly with WireViz Doc's templating system.

## Overview

Instead of writing SVG/Jinja2 code by hand, you can:

1. **Design your template visually** in Inkscape or Illustrator
2. **Mark placeholder elements** with specific IDs and placeholder text
3. **Export as plain SVG**
4. **WireViz Doc replaces placeholders** with actual content at build time

## Quick Start

1. Open `templates/sheet-a4-editable.svg` in Inkscape
2. Modify the layout, fonts, colors, logo, etc.
3. Keep the placeholder IDs and text markers intact
4. Save as Plain SVG
5. Rename to `.svg.j2` for Jinja2 processing (or use ID-based replacement)

---

## Method 1: ID-Based Replacement (Recommended)

This method uses SVG element IDs that the code targets directly. No Jinja2 syntax in the SVG file.

### Setting Element IDs in Inkscape

1. Select an element (text, rectangle, group)
2. Open **Object → Object Properties** (Ctrl+Shift+O)
3. Set a meaningful **ID** (e.g., `title-text`, `diagram-area`, `bom-table`)
4. Click **Set**

### Required Element IDs

| Element ID | Type | Purpose |
|------------|------|---------|
| `doc-id` | text | Document ID (e.g., "HAR-0007") |
| `doc-title` | text | Document title |
| `doc-revision` | text | Revision letter/number |
| `doc-date` | text | Document date |
| `doc-author` | text | Author name |
| `doc-approver` | text | Approver name (optional) |
| `doc-project` | text | Project name |
| `doc-sheet` | text | Sheet number (e.g., "1 of 2") |
| `diagram-area` | rect/group | Area where diagram SVG is inserted |
| `bom-area` | rect/group | Area for BOM table |
| `wiring-area` | rect/group | Area for wiring table |
| `notes-area` | text/group | Notes section |

### Example Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Design in Inkscape                                          │
│     - Create title block with text elements                     │
│     - Draw rectangles for content areas                         │
│     - Assign IDs to all dynamic elements                        │
│                                                                 │
│  2. Export as Plain SVG                                         │
│     File → Save As → Plain SVG (*.svg)                          │
│                                                                 │
│  3. WireViz Doc processes the template                          │
│     - Finds elements by ID                                      │
│     - Replaces text content                                     │
│     - Inserts diagram/tables into area elements                 │
│                                                                 │
│  4. Output: Final populated SVG/PDF                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Method 2: Placeholder Text Replacement

Use placeholder text that gets replaced. Simpler but less flexible.

### Placeholder Markers

Use double-bracket markers in your text elements:

| Placeholder | Replaced With |
|-------------|---------------|
| `{{DOC_ID}}` | Harness ID |
| `{{TITLE}}` | Document title |
| `{{REVISION}}` | Revision |
| `{{DATE}}` | Date |
| `{{AUTHOR}}` | Author |
| `{{APPROVER}}` | Approver |
| `{{PROJECT}}` | Project name |
| `{{SHEET}}` | Sheet number |
| `{{TOTAL_SHEETS}}` | Total sheets |

### In Inkscape

1. Create a text element
2. Type the placeholder: `{{TITLE}}`
3. Style the text (font, size, color) - styling is preserved
4. The placeholder text is replaced but formatting remains

---

## Method 3: Jinja2 Templates (Advanced)

For complex logic (loops, conditionals), save as `.svg.j2` and use Jinja2 syntax.

### When to Use Jinja2

- BOM tables with variable row counts
- Conditional sections (show/hide based on data)
- Loops over connections or parts
- Computed values

### Hybrid Approach

Design the static parts visually, then add Jinja2 for dynamic tables:

```xml
<!-- Designed in Inkscape -->
<text id="doc-title">{{TITLE}}</text>

<!-- Hand-coded Jinja2 for dynamic table -->
<g id="bom-table">
  {% for item in bom %}
  <text y="{{ 100 + loop.index * 20 }}">{{ item.pn }}</text>
  {% endfor %}
</g>
```

---

## Template Design Guidelines

### Page Setup (Inkscape)

1. **File → Document Properties**
2. Set page size:
   - A4 Landscape: 297mm × 210mm
   - A3 Landscape: 420mm × 297mm
   - Letter Landscape: 11in × 8.5in
3. Set display units to mm
4. Enable "Show page border"

### Recommended Layout (A4 Landscape)

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │                                                          │  │
│  │                    DIAGRAM AREA                          │  │
│  │                    id="diagram-area"                     │  │
│  │                    (200mm × 120mm)                       │  │
│  │                                                          │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │      BOM TABLE          │  │      WIRING TABLE           │  │
│  │   id="bom-area"         │  │   id="wiring-area"          │  │
│  │   (95mm × 50mm)         │  │   (95mm × 50mm)             │  │
│  └─────────────────────────┘  └─────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    TITLE BLOCK                           │  │
│  │  ID | Title | Rev | Date | Author | Approver | Sheet     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### Font Recommendations

Use fonts that are:
- **Cross-platform**: Arial, Helvetica, Liberation Sans
- **Monospace for data**: Consolas, Liberation Mono, Courier New
- **Embedded or converted to paths** for guaranteed rendering

To convert text to paths (prevents font issues):
- Inkscape: **Path → Object to Path** (only for static text like "TITLE:", "REV:")
- Keep dynamic text as text elements (so content can be replaced)

### Color Scheme

| Element | Recommended Color |
|---------|-------------------|
| Border/lines | `#000000` (black) |
| Header text | `#000000` (black) |
| Data text | `#333333` (dark gray) |
| Table headers | `#E5E5E5` (light gray background) |
| Pair highlighting | `#F0F8FF` (alice blue) |

### Stroke Widths

| Element | Width |
|---------|-------|
| Page border | 0.5mm |
| Title block borders | 0.35mm |
| Table lines | 0.25mm |
| Zone dividers | 0.1mm |

---

## Inkscape-Specific Tips

### Layers

Organize your template with layers:
- **Background** - Page border, zone markers
- **Title Block** - Title block elements
- **Content Areas** - Rectangles marking diagram/table areas
- **Static Text** - Labels like "TITLE:", "REV:", "DATE:"
- **Dynamic Text** - Placeholder text elements

### Alignment

1. Select elements to align
2. **Object → Align and Distribute** (Ctrl+Shift+A)
3. Use "Relative to: Page" for consistent positioning

### Snapping

Enable snapping for precise layout:
- **View → Snap** (%)
- Enable "Snap to grid" and "Snap to guides"

### Export Settings

**File → Save As → Plain SVG**

Important: Use "Plain SVG", not "Inkscape SVG" to avoid Inkscape-specific extensions that may cause issues.

---

## Illustrator-Specific Tips

### Artboard Setup

1. **File → New**
2. Set dimensions (297mm × 210mm for A4 landscape)
3. Color mode: RGB (for screen) or CMYK (for print)

### Naming Layers/Elements

1. **Window → Layers**
2. Double-click layer/element to rename
3. Use the ID naming convention (e.g., `doc-title`)

### Export Settings

**File → Export → Export As → SVG**

Options:
- Styling: Inline Style
- Font: Convert to Outlines (for static text only)
- Images: Embed
- Object IDs: Layer Names (important!)
- Minify: No
- Responsive: No (use fixed dimensions)

---

## Testing Your Template

### Validate the SVG

```bash
# Check SVG is valid XML
xmllint --noout your-template.svg

# List all element IDs
grep -o 'id="[^"]*"' your-template.svg | sort | uniq
```

### Required IDs Checklist

Run this to verify required IDs are present:

```bash
#!/bin/bash
TEMPLATE="your-template.svg"
REQUIRED_IDS="doc-id doc-title doc-revision doc-date doc-author diagram-area"

for id in $REQUIRED_IDS; do
  if grep -q "id=\"$id\"" "$TEMPLATE"; then
    echo "✓ Found: $id"
  else
    echo "✗ Missing: $id"
  fi
done
```

### Preview with Sample Data

```bash
# Once the renderer is implemented
wvdoc preview --template your-template.svg --sample-data
```

---

## Example: Creating a Custom Template

### Step 1: Start from Base Template

```bash
cp src/wireviz_doc/templates/sheet-a4-editable.svg my-company-template.svg
inkscape my-company-template.svg
```

### Step 2: Customize in Inkscape

1. Replace placeholder logo with your company logo
2. Adjust colors to match company branding
3. Modify title block layout if needed
4. Add any additional fields (cost center, department, etc.)

### Step 3: Verify IDs

After editing, verify IDs are intact:
- Open **Edit → XML Editor** (Ctrl+Shift+X)
- Navigate through elements
- Confirm IDs match expected values

### Step 4: Save and Test

1. **File → Save As → Plain SVG**
2. Run validation script
3. Test with a sample harness file

---

## Troubleshooting

### Text Not Replacing

- Verify the element ID is exactly correct (case-sensitive)
- Check the element is a `<text>` or `<tspan>` element
- Ensure no Inkscape namespacing issues (save as Plain SVG)

### Diagram Not Fitting

- Check `diagram-area` rectangle dimensions
- Verify the rectangle has `id="diagram-area"` attribute
- Diagram is scaled to fit within the rectangle bounds

### Fonts Look Wrong

- Convert static labels to paths
- Use web-safe fonts for dynamic text
- Embed fonts if using custom fonts

### SVG Not Valid

- Save as Plain SVG, not Inkscape SVG
- Remove any invalid characters in IDs
- Check for unclosed elements with `xmllint`

---

## File Locations

| File | Purpose |
|------|---------|
| `src/wireviz_doc/templates/sheet-a4-editable.svg` | Base template for Inkscape editing |
| `src/wireviz_doc/templates/sheet-a4.svg.j2` | Jinja2 template (code-based) |
| `examples/templates/` | Example custom templates |
| `assets/logos/` | Company logos for templates |
