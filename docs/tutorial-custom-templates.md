# Tutorial: Creating Custom Output Templates

This tutorial walks you through creating a custom template for your organization's wiring documentation. By the end, you'll have a branded template that produces professional factory-ready output.

## What You'll Learn

- How to open and edit the base template in Inkscape
- Adding your company logo and branding
- Customizing the layout for your needs
- Testing your template with a sample harness
- Troubleshooting common issues

## Prerequisites

- [Inkscape](https://inkscape.org/release/) installed (free, open source)
- Basic familiarity with vector graphics editing
- A sample harness YAML file to test with

---

## Step 1: Open the Base Template

The base template is located at:
```
src/wireviz_doc/templates/sheet-a4-editable.svg
```

**Copy it first** - don't edit the original:

```bash
cp src/wireviz_doc/templates/sheet-a4-editable.svg my-company-template.svg
```

Open your copy in Inkscape:

```bash
inkscape my-company-template.svg
```

You'll see a template with labeled placeholder areas:

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────┐  ┌──────────────────────────┐  │
│  │                         │  │         NOTES            │  │
│  │                         │  └──────────────────────────┘  │
│  │      DIAGRAM AREA       │  ┌──────────────────────────┐  │
│  │                         │  │    REVISION HISTORY      │  │
│  │                         │  └──────────────────────────┘  │
│  │                         │  ┌──────────────────────────┐  │
│  └─────────────────────────┘  │     WIRING TABLE         │  │
│  ┌─────────────────────────┐  └──────────────────────────┘  │
│  │       BOM TABLE         │  ┌──────────────────────────┐  │
│  │                         │  │       TITLE BLOCK        │  │
│  └─────────────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 2: Understand the Template Structure

### Layers

Open the Layers panel (**Layer → Layers and Objects** or Ctrl+Shift+L).

The template uses these logical groups:
- **diagram-area-group** - Where the WireViz diagram appears
- **bom-area-group** - Bill of materials table
- **notes-area-group** - Notes section
- **revision-area-group** - Revision history
- **title-block** - Title block with metadata
- **wiring-area-group** - Wiring schedule table
- **zone-markers** - Optional drawing zone references

### Element IDs

The rendering engine finds elements by their ID. View IDs in the XML Editor (**Edit → XML Editor** or Ctrl+Shift+X).

Critical IDs to preserve:

| ID | What It Does |
|----|--------------|
| `diagram-area` | Rectangle defining where diagram is inserted |
| `bom-area` | Rectangle for BOM table insertion |
| `doc-title` | Text element for document title |
| `doc-id` | Text element for harness ID |
| `doc-revision` | Text element for revision |
| `doc-date` | Text element for date |
| `doc-author` | Text element for author name |
| `doc-approver` | Text element for approver name |
| `doc-project` | Text element for project name |
| `doc-sheet` | Text element for sheet number |

**Rule: You can move, resize, and restyle elements, but don't delete or rename their IDs.**

---

## Step 3: Add Your Company Logo

1. **Select the logo placeholder text** ("Your Company Name" in the title block)

2. **Delete it** (we'll replace with an image)

3. **Import your logo**: File → Import (Ctrl+I)
   - Select your logo file (SVG, PNG, or JPG)
   - PNG/JPG: Choose "Embed" when prompted

4. **Position the logo** in the title block area (top-left cell)

5. **Scale to fit**: Hold Ctrl while dragging corners to maintain aspect ratio

6. **Optionally set an ID**: Object → Object Properties, set ID to `company-logo`

### Logo Tips

- **SVG logos** scale better than raster images
- Keep logos simple - complex logos may not render well at small sizes
- Target size: approximately 35mm × 10mm for the default title block

---

## Step 4: Customize Colors and Fonts

### Changing Colors

1. Open the CSS in the XML Editor:
   - Edit → XML Editor
   - Navigate to `svg > defs > style`
   - Edit the CDATA content

2. Or select elements and use the Fill/Stroke panel (Ctrl+Shift+F)

### Example: Change border color to dark blue

Find in the CSS:
```css
.border { fill: none; stroke: #000000; stroke-width: 0.5; }
```

Change to:
```css
.border { fill: none; stroke: #003366; stroke-width: 0.5; }
```

### Changing Fonts

The default fonts are system fonts for compatibility:
- **Labels**: Arial/Helvetica
- **Values**: Arial/Helvetica Bold
- **Monospace**: Consolas/Liberation Mono

To change fonts:
1. Select text elements
2. Use the text toolbar or Text → Text and Font (Ctrl+Shift+T)

**Warning**: Custom fonts must be installed on all systems that render the template, or convert static text to paths.

---

## Step 5: Adjust the Layout

### Moving Content Areas

The dashed rectangles define where dynamic content is inserted. You can:

- **Move them**: Select and drag, or use arrow keys for precise positioning
- **Resize them**: Drag corners or edges
- **Reposition**: Object → Transform (Ctrl+Shift+M) for exact coordinates

### Example: Make the Diagram Area Larger

1. Select the rectangle with `id="diagram-area"`
2. Drag the bottom edge down to give more space
3. Move the BOM area down to accommodate
4. Adjust the title block position if needed

### Removing Optional Sections

Don't need revision history? Delete the entire `revision-area-group`:

1. Select the group in Layers panel
2. Delete (Del key)

The renderer will skip missing optional areas.

---

## Step 6: Customize the Title Block

The title block contains your document metadata. Customize it for your organization.

### Adding Custom Fields

Want to add a "Cost Center" field?

1. Copy an existing label+value pair (e.g., select both "SCALE" elements)
2. Paste (Ctrl+V)
3. Move to desired position
4. Edit the label text to "COST CENTER"
5. Set the value element's ID to `doc-cost-center`
6. Update the harness YAML to include this in `custom_fields`

### Removing Unused Fields

If you don't use "Scale" or "Units":

1. Select those text elements
2. Delete them
3. Adjust spacing of remaining elements

---

## Step 7: Save Your Template

**Important: Save as Plain SVG**

1. File → Save As
2. Choose "Plain SVG (*.svg)" - NOT "Inkscape SVG"
3. Save to your project's templates directory

Plain SVG removes Inkscape-specific data that can cause rendering issues.

---

## Step 8: Test Your Template

### Validate the SVG Structure

```bash
# Check for valid XML
xmllint --noout my-company-template.svg

# Verify required IDs exist
grep -o 'id="doc-[^"]*"' my-company-template.svg
grep -o 'id=".*-area"' my-company-template.svg
```

### Generate Test Output

```bash
# Build with your custom template
wvdoc build examples/demo-harness.harness.yml \
  --template my-company-template.svg \
  --output-dir test-output/

# View the result
open test-output/HAR-DEMO-001/diagram.svg  # macOS
xdg-open test-output/HAR-DEMO-001/diagram.svg  # Linux
```

### Check the Output

Verify:
- [ ] Company logo appears correctly
- [ ] Title block fields are populated
- [ ] Diagram fits within the diagram area
- [ ] BOM table is readable
- [ ] Colors and fonts look correct
- [ ] PDF export works: check `diagram.pdf`

---

## Step 9: Install Your Template

Once tested, install your template for regular use:

```bash
# Copy to the templates directory
cp my-company-template.svg src/wireviz_doc/templates/

# Or set as default in config
echo 'template: my-company-template.svg' >> .wvdoc.yml
```

### Config File Option

Create `.wvdoc.yml` in your project:

```yaml
template: my-company-template.svg
output_dir: build
formats:
  - svg
  - pdf
```

---

## Common Customizations

### A3 Page Size

1. File → Document Properties
2. Set width: 420mm, height: 297mm
3. Resize all elements proportionally
4. Save as `sheet-a3-company.svg`

### Portrait Orientation

1. File → Document Properties
2. Swap width and height (210mm × 297mm for A4)
3. Reorganize the layout - typically:
   - Diagram at top
   - BOM below diagram
   - Title block at bottom

### Multi-Page Templates

Create separate templates for different page types:

- `sheet-first.svg` - First page with diagram and title block
- `sheet-continuation.svg` - Continuation pages for long BOMs/wiring tables

---

## Troubleshooting

### "Element not found: doc-title"

The ID was renamed or deleted. Check in XML Editor that `id="doc-title"` exists on a text element.

### Logo Doesn't Appear

- Ensure the logo is embedded, not linked
- Check the logo isn't outside the page bounds
- Verify the logo group isn't hidden (check layer visibility)

### Fonts Look Wrong in PDF

- Use system fonts (Arial, Helvetica)
- Or convert text to paths: Path → Object to Path
- Note: Only convert static labels, not dynamic text!

### Diagram Overflows the Area

- Make `diagram-area` rectangle larger
- Or the diagram may need manual scaling in WireViz

### Colors Don't Match

- Ensure you're editing the correct CSS class
- Check for inline styles overriding CSS
- Verify color format (#RRGGBB)

---

## Next Steps

- Read the full [Template Design Guide](template-design.md) for advanced techniques
- Explore [Jinja2 templating](template-design.md#method-3-jinja2-templates-advanced) for complex layouts
- Set up [CI/CD integration](integration.md) with your custom template

---

## Quick Reference

### Required Element IDs

```
doc-id          Document identifier
doc-title       Document title
doc-revision    Revision letter/number
doc-date        Document date
doc-author      Author name
doc-approver    Approver name
doc-project     Project name
doc-sheet       Sheet number
diagram-area    Diagram insertion rectangle
bom-area        BOM table insertion rectangle
```

### Inkscape Shortcuts

| Action | Shortcut |
|--------|----------|
| Object Properties (set ID) | Ctrl+Shift+O |
| XML Editor | Ctrl+Shift+X |
| Layers Panel | Ctrl+Shift+L |
| Align & Distribute | Ctrl+Shift+A |
| Transform | Ctrl+Shift+M |
| Import | Ctrl+I |
| Save As | Ctrl+Shift+S |

### Validation Commands

```bash
# Validate XML
xmllint --noout template.svg

# List all IDs
grep -oP 'id="\K[^"]+' template.svg | sort

# Check required IDs
for id in doc-id doc-title diagram-area bom-area; do
  grep -q "id=\"$id\"" template.svg && echo "✓ $id" || echo "✗ $id"
done
```
