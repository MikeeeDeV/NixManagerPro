import customtkinter as ctk
from ui.modern_dialog import (
    ModernConfirmDialog,
    ModernAlertDialog,
    show_confirm_dialog,
    show_alert_dialog,
)


def test_modern_confirm_dialog_confirm():
    root = ctk.CTk()
    dialog = ModernConfirmDialog(
        root,
        title="Confirm Deep Purge",
        message="This will completely eradicate selected packages.",
        details=["Remove package binaries", "Eradicate cache"],
        items=["discord [Snap]", "vlc [Nix]"],
        danger=True,
        confirm_text="Purge",
    )
    assert not dialog.result
    dialog._on_confirm()
    assert bool(dialog.result) is True
    root.destroy()


def test_modern_confirm_dialog_cancel():
    root = ctk.CTk()
    dialog = ModernConfirmDialog(
        root,
        title="Confirm Uninstall",
        message="Uninstall package?",
        danger=False,
    )
    dialog._on_cancel()
    assert not dialog.result
    root.destroy()


def test_modern_alert_dialog_init():
    root = ctk.CTk()
    dlg = ModernAlertDialog(root, title="Info Alert", message="Operation completed.", alert_type="info")
    assert dlg.title() == "Info Alert"
    dlg._safe_grab()
    dlg.destroy()
    root.destroy()


def test_app_details_dialog_init():
    from core.catalog import CatalogItem
    from ui.app_details_dialog import AppDetailsDialog

    root = ctk.CTk()
    item = CatalogItem(
        name="TestApp",
        attr="testapp",
        category="General",
        description="A test package description",
        homepage="https://example.com",
        license="MIT",
    )
    dlg = AppDetailsDialog(root, item=item, source="Snap")
    assert dlg.title() == "TestApp — Package Details"
    assert dlg._name_lbl.cget("text") == "TestApp"
    assert dlg._desc_lbl.cget("text") == "A test package description"
    dlg._safe_grab()
    dlg.destroy()
    root.destroy()

