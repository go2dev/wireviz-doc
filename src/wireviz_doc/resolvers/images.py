"""
Image resolution module for WireViz Doc.

Resolves image paths for parts, connectors, and cables by checking:
1. Explicit path specified in YAML
2. Local file: <Manufacturer>_<MPN>.(png|jpg|jpeg|svg)
3. Local file: <PN>.(png|jpg|jpeg|svg)

Usage:
    from wireviz_doc.resolvers.images import resolve_images

    image_paths = resolve_images(document, search_dirs=["assets/images"])
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Union

from wireviz_doc.models.document import HarnessDocument
from wireviz_doc.output import logger


# Supported image extensions
IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".svg", ".gif"]


def _sanitize_filename(name: str) -> str:
    """
    Sanitize a string for use in a filename.

    Removes or replaces characters that are problematic in filenames.
    """
    # Replace common problematic characters
    sanitized = name.replace("/", "-").replace("\\", "-")
    sanitized = sanitized.replace(" ", "_")
    sanitized = sanitized.replace(":", "-")

    # Remove other special characters
    sanitized = re.sub(r'[<>"|?*]', "", sanitized)

    # Remove consecutive underscores/hyphens
    sanitized = re.sub(r'[-_]+', "_", sanitized)

    return sanitized.strip("_-")


def _find_image_file(
    base_name: str,
    search_dirs: List[Path],
) -> Optional[Path]:
    """
    Search for an image file with the given base name in search directories.

    Tries all supported extensions.
    """
    for search_dir in search_dirs:
        for ext in IMAGE_EXTENSIONS:
            # Try exact match
            candidate = search_dir / f"{base_name}{ext}"
            if candidate.exists():
                return candidate

            # Try case-insensitive match (for case-insensitive filesystems)
            candidate_lower = search_dir / f"{base_name.lower()}{ext}"
            if candidate_lower.exists():
                return candidate_lower

    return None


def resolve_image_for_part(
    manufacturer: str,
    mpn: str,
    primary_pn: str,
    explicit_path: Optional[str],
    search_dirs: List[Path],
    base_path: Optional[Path] = None,
) -> Optional[Path]:
    """
    Resolve image path for a part.

    Resolution order:
    1. Explicit path from YAML (if valid)
    2. <Manufacturer>_<MPN>.(ext)
    3. <PN>.(ext)

    Args:
        manufacturer: Part manufacturer.
        mpn: Manufacturer part number.
        primary_pn: Primary/internal part number.
        explicit_path: Explicit path from YAML (if any).
        search_dirs: List of directories to search.
        base_path: Base path for resolving relative explicit paths.

    Returns:
        Resolved Path to the image, or None if not found.
    """
    # 1. Check explicit path
    if explicit_path:
        explicit = Path(explicit_path)

        # If relative, try relative to base_path first
        if not explicit.is_absolute() and base_path:
            candidate = base_path / explicit
            if candidate.exists():
                return candidate

        # Try each search directory
        for search_dir in search_dirs:
            candidate = search_dir / explicit
            if candidate.exists():
                return candidate

        # Try as absolute path
        if explicit.is_absolute() and explicit.exists():
            return explicit

    # 2. Try <Manufacturer>_<MPN>
    if manufacturer and mpn:
        mfr_mpn_name = f"{_sanitize_filename(manufacturer)}_{_sanitize_filename(mpn)}"
        found = _find_image_file(mfr_mpn_name, search_dirs)
        if found:
            return found

    # 3. Try <PN>
    if primary_pn:
        pn_name = _sanitize_filename(primary_pn)
        found = _find_image_file(pn_name, search_dirs)
        if found:
            return found

    return None


def resolve_images(
    document: HarnessDocument,
    search_dirs: Optional[List[Union[str, Path]]] = None,
    base_path: Optional[Union[str, Path]] = None,
) -> Dict[str, str]:
    """
    Resolve all image paths for a HarnessDocument.

    Returns a dictionary mapping component IDs to resolved image paths.

    Args:
        document: The HarnessDocument to resolve images for.
        search_dirs: List of directories to search for images.
                     Defaults to ["assets/images", "images"].
        base_path: Base path for resolving relative paths.

    Returns:
        Dict mapping component ID to resolved image path string.

    Example:
        >>> paths = resolve_images(document, search_dirs=["assets/images"])
        >>> print(paths)
        {'J1': 'assets/images/Molex_39-01-2040.png', 'W1': None}
    """
    if search_dirs is None:
        search_dirs = [Path("assets/images"), Path("images")]
    else:
        search_dirs = [Path(d) for d in search_dirs]

    if base_path:
        base_path = Path(base_path)

    resolved: Dict[str, str] = {}

    # Resolve connector images
    for conn_id, connector in document.connectors.items():
        explicit = connector.image.src if connector.image else None

        path = resolve_image_for_part(
            manufacturer=connector.manufacturer,
            mpn=connector.mpn,
            primary_pn=connector.primary_pn,
            explicit_path=explicit,
            search_dirs=search_dirs,
            base_path=base_path,
        )

        if path:
            resolved[conn_id] = str(path)
            logger.debug(f"Resolved image for connector {conn_id}: {path}")
        else:
            logger.debug(f"No image found for connector {conn_id}")

    # Resolve cable images
    for cable_id, cable in document.cables.items():
        explicit = cable.image.src if cable.image else None

        path = resolve_image_for_part(
            manufacturer=cable.manufacturer,
            mpn=cable.mpn,
            primary_pn=cable.primary_pn,
            explicit_path=explicit,
            search_dirs=search_dirs,
            base_path=base_path,
        )

        if path:
            resolved[cable_id] = str(path)
            logger.debug(f"Resolved image for cable {cable_id}: {path}")
        else:
            logger.debug(f"No image found for cable {cable_id}")

    # Resolve part images
    for part_id, part in document.parts.items():
        explicit = part.image.src if part.image else None

        path = resolve_image_for_part(
            manufacturer=part.manufacturer,
            mpn=part.mpn,
            primary_pn=part.primary_pn,
            explicit_path=explicit,
            search_dirs=search_dirs,
            base_path=base_path,
        )

        if path:
            resolved[part_id] = str(path)
            logger.debug(f"Resolved image for part {part_id}: {path}")

    logger.info(f"Resolved {len(resolved)} image paths")
    return resolved


def get_missing_images(
    document: HarnessDocument,
    search_dirs: Optional[List[Union[str, Path]]] = None,
    base_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, str]]:
    """
    Get a list of components that are missing images.

    Useful for validation and image collection workflows.

    Args:
        document: The HarnessDocument.
        search_dirs: List of directories to search.
        base_path: Base path for resolving relative paths.

    Returns:
        List of dicts with component info for missing images.
    """
    resolved = resolve_images(document, search_dirs, base_path)
    missing = []

    # Check connectors
    for conn_id, connector in document.connectors.items():
        if conn_id not in resolved:
            missing.append({
                "type": "connector",
                "id": conn_id,
                "manufacturer": connector.manufacturer,
                "mpn": connector.mpn,
                "pn": connector.primary_pn,
                "suggested_filename": f"{_sanitize_filename(connector.manufacturer)}_{_sanitize_filename(connector.mpn)}.png",
            })

    # Check cables
    for cable_id, cable in document.cables.items():
        if cable_id not in resolved:
            missing.append({
                "type": "cable",
                "id": cable_id,
                "manufacturer": cable.manufacturer,
                "mpn": cable.mpn,
                "pn": cable.primary_pn,
                "suggested_filename": f"{_sanitize_filename(cable.manufacturer)}_{_sanitize_filename(cable.mpn)}.png",
            })

    return missing


def validate_image_paths(
    resolved_paths: Dict[str, str],
) -> List[str]:
    """
    Validate that all resolved image paths actually exist.

    Args:
        resolved_paths: Dict of component IDs to image paths.

    Returns:
        List of error messages for invalid paths.
    """
    errors = []

    for component_id, path in resolved_paths.items():
        if not Path(path).exists():
            errors.append(f"Image file not found for {component_id}: {path}")

    return errors
