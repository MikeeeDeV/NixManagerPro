from core.catalog import (
    CURATED_PACKAGES,
    get_catalog_categories,
    get_catalog_item,
    resolve_rich_details,
    search_catalog,
)


def test_catalog_has_entries():
    assert len(CURATED_PACKAGES) >= 20


def test_catalog_search():
    results = search_catalog("git")
    assert any(r.name == "Git" for r in results)

    dev_tools = search_catalog("", category="Development")
    assert len(dev_tools) > 0
    assert all(r.category == "Development" for r in dev_tools)


def test_get_catalog_item():
    item = get_catalog_item("vscodium")
    assert item is not None
    assert "vscodium" in item.attr.lower()
    assert item.license == "MIT"


def test_resolve_rich_details_fallback():
    item = resolve_rich_details("some-custom-tool", source="Snap")
    assert item.name == "Some-Custom-Tool"
    assert "Snap" in item.description


def test_app_details_dialog_safe_init():
    import customtkinter as ctk
    from ui.app_details_dialog import AppDetailsDialog
    root = ctk.CTk()
    item = resolve_rich_details("git", source="Nix")
    dialog = AppDetailsDialog(root, item=item, source="Nix")
    assert dialog.title().startswith("Git")
    # Verify _safe_grab does not raise
    dialog._safe_grab()
    dialog.destroy()
    root.destroy()

