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
    assert dialog.result is False
    dialog._on_confirm()
    assert dialog.result is True
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
    assert dialog.result is False
    root.destroy()


def test_modern_alert_dialog_init():
    root = ctk.CTk()
    dlg = ModernAlertDialog(root, title="Info Alert", message="Operation completed.", alert_type="info")
    assert dlg.title() == "Info Alert"
    dlg._safe_grab()
    dlg.destroy()
    root.destroy()
