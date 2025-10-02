from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from fastapi import HTTPException


BASE_DIR = Path(__file__).resolve().parents[3]
CATALOG_METADATA_PATH = BASE_DIR / "assets" / "catalog_metadata.yaml"


def _normalize_component(value: str) -> str:
    value_str = str(value).strip()
    if not value_str:
        raise HTTPException(status_code=400, detail="ID component must not be empty")
    if not value_str.isdigit():
        raise HTTPException(status_code=400, detail="ID component must be numeric")
    if len(value_str) == 1:
        return value_str.zfill(2)
    return value_str


def _build_page_key(category_id: str, book_id: str, story_id: str, page_id: str) -> str:
    components = (
        _normalize_component(category_id),
        _normalize_component(book_id),
        _normalize_component(story_id),
        _normalize_component(page_id),
    )
    return "".join(components)


def _load_catalog_pages() -> Dict[str, Dict[str, Any]]:
    if not CATALOG_METADATA_PATH.exists():
        raise HTTPException(status_code=500, detail="Catalog metadata file not found")

    try:
        with CATALOG_METADATA_PATH.open("r", encoding="utf-8") as metadata_file:
            catalog_data = yaml.safe_load(metadata_file) or {}
    except yaml.YAMLError as yaml_error:
        raise HTTPException(status_code=500, detail=f"Invalid catalog metadata format: {yaml_error}")

    pages = catalog_data.get("pages")
    if not isinstance(pages, dict):
        raise HTTPException(status_code=500, detail="Catalog metadata missing 'pages' mapping")

    return pages


def _find_page_key(pages: Dict[str, Dict[str, Any]], category_id: str, book_id: str, story_id: str, page_id: str) -> Optional[str]:
    normalized_category = _normalize_component(category_id)
    normalized_book = _normalize_component(book_id)
    normalized_story = _normalize_component(story_id)
    normalized_page = _normalize_component(page_id)

    direct_key = _build_page_key(category_id, book_id, story_id, page_id)
    if direct_key in pages:
        return direct_key

    for page_key, page_data in pages.items():
        if not isinstance(page_data, dict):
            continue

        if (
            str(page_data.get("category_id", "")).zfill(2) == normalized_category
            and str(page_data.get("book_id", "")).zfill(2) == normalized_book
            and str(page_data.get("story_id", "")).zfill(2) == normalized_story
            and str(page_data.get("page_id", "")).zfill(2) == normalized_page
        ):
            return page_key

    return None


def get_page_id(category_id: str, book_id: str, story_id: str, page_id: str) -> str:
    pages = _load_catalog_pages()
    page_key = _find_page_key(
        pages,
        category_id=category_id,
        book_id=book_id,
        story_id=story_id,
        page_id=page_id,
    )

    if page_key is None:
        raise HTTPException(status_code=404, detail="Page ID not found for provided identifiers")

    return page_key
