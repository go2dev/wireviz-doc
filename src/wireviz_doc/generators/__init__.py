"""Document generators for wireviz-doc.

This package provides generators for various output formats:
- wireviz_yaml: Generate WireViz-compatible YAML
- wiring_table: Generate wiring tables (TSV, HTML)
- bom: Generate Bill of Materials (TSV, HTML)
"""

from wireviz_doc.generators.bom import (
    generate_bom_html,
    generate_bom_svg_snippet,
    generate_bom_tsv,
    generate_bom_tsv_file,
    get_bom_data,
)
from wireviz_doc.generators.wireviz_yaml import (
    generate_wireviz_yaml,
    generate_wireviz_yaml_file,
)
from wireviz_doc.generators.wiring_table import (
    generate_wiring_table_html,
    generate_wiring_table_svg_snippet,
    generate_wiring_table_tsv,
    generate_wiring_table_tsv_file,
)

__all__ = [
    # WireViz YAML
    "generate_wireviz_yaml",
    "generate_wireviz_yaml_file",
    # Wiring table
    "generate_wiring_table_tsv",
    "generate_wiring_table_tsv_file",
    "generate_wiring_table_html",
    "generate_wiring_table_svg_snippet",
    # BOM
    "generate_bom_tsv",
    "generate_bom_tsv_file",
    "generate_bom_html",
    "generate_bom_svg_snippet",
    "get_bom_data",
]
