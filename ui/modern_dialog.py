"""
ui.modern_dialog
~~~~~~~~~~~~~~~~

State-of-the-art CustomTkinter modal dialog suite:
Replaces dated Tkinter OS messageboxes with sleek, high-contrast,
theme-adaptive confirmation and alert dialogs.
"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from typing import List, Optional, Sequence

import customtkinter as ctk

from utils.icons import get_icon


class ModernConfirmDialog(ctk.CTkToplevel):
    """
    Modern modal dialog for confirming actions, particularly destructive
    operations such as Deep Purge, Rollback, or Package Uninstallation.
    """

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        message: str,
        details: Optional[Sequence[str]] = None,
        items: Optional[Sequence[str]] = None,
        danger: bool = False,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
    ) -> None:
        top_parent = parent.winfo_toplevel() if hasattr(parent, "winfo_toplevel") else parent
        super().__init__(top_parent)

        self.result: bool = False
        self.title(title)
        self.resizable(False, False)

        # Theme and layout
        self.grid_columnconfigure(0, weight=1)

        # Center relative to parent
        try:
            self.transient(top_parent)
        except Exception:
            pass

        # Load icon
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "nixmanager.png"
        if icon_path.exists():
            try:
                self._app_icon = tk.PhotoImage(file=str(icon_path))
                self.iconphoto(True, self._app_icon)
            except Exception:
                pass

        # ---- 1. Header Frame ----------------------------------------------
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))
        header.grid_columnconfigure(1, weight=1)

        badge_color = ("#fadbd8", "#78281f") if danger else ("#d4e6f1", "#1b4f72")
        icon_img = get_icon("purge" if danger else "shield", (28, 28))
        icon_lbl = ctk.CTkLabel(
            header,
            text="",
            image=icon_img,
            width=52,
            height=52,
            fg_color=badge_color,
            corner_radius=14,
        )
        icon_lbl.grid(row=0, column=0, rowspan=2, padx=(0, 14), sticky="nw")

        title_lbl = ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        )
        title_lbl.grid(row=0, column=1, sticky="w")

        msg_lbl = ctk.CTkLabel(
            header,
            text=message,
            font=ctk.CTkFont(size=13),
            text_color=("gray30", "gray70"),
            wraplength=420,
            justify="left",
            anchor="w",
        )
        msg_lbl.grid(row=1, column=1, sticky="w", pady=(2, 0))

        current_row = 1

        # ---- 2. Consequence / Detail Bullets --------------------------------
        if details:
            details_box = ctk.CTkFrame(
                self,
                fg_color=("gray92", "gray17"),
                border_width=1,
                border_color=("#e74c3c" if danger else ("gray80", "gray30")),
                corner_radius=10,
            )
            details_box.grid(row=current_row, column=0, sticky="ew", padx=24, pady=(4, 10))

            for bullet in details:
                b_row = ctk.CTkFrame(details_box, fg_color="transparent")
                b_row.pack(fill="x", padx=12, pady=4)

                bullet_dot = "-" if danger else "•"
                dot_color = "#e74c3c" if danger else "#3498db"
                ctk.CTkLabel(
                    b_row,
                    text=bullet_dot,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=dot_color,
                    width=16,
                ).pack(side="left", padx=(0, 6))

                ctk.CTkLabel(
                    b_row,
                    text=bullet,
                    font=ctk.CTkFont(size=12),
                    wraplength=400,
                    justify="left",
                    anchor="w",
                ).pack(side="left", fill="x", expand=True)

            current_row += 1

        # ---- 3. Target Items Pill Badges -----------------------------------
        if items:
            items_box = ctk.CTkFrame(self, fg_color="transparent")
            items_box.grid(row=current_row, column=0, sticky="ew", padx=24, pady=(2, 10))

            ctk.CTkLabel(
                items_box,
                text="Target Package(s):",
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
            ).pack(anchor="w", pady=(0, 4))

            pills_frame = ctk.CTkFrame(items_box, fg_color="transparent")
            pills_frame.pack(fill="x")

            for item_name in items[:6]:  # Show up to 6 targets neatly
                pill = ctk.CTkLabel(
                    pills_frame,
                    text=item_name,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color=("gray85", "gray25"),
                    corner_radius=6,
                    padx=10,
                    pady=4,
                )
                pill.pack(side="left", padx=(0, 6), pady=2)

            if len(items) > 6:
                ctk.CTkLabel(
                    pills_frame,
                    text=f"+{len(items) - 6} more",
                    font=ctk.CTkFont(size=11),
                    text_color="gray",
                ).pack(side="left", padx=4)

            current_row += 1

        # ---- 4. Action Buttons (Footer) -----------------------------------
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=current_row, column=0, sticky="ew", padx=24, pady=(14, 20))

        cancel_btn = ctk.CTkButton(
            footer,
            text=cancel_text,
            width=110,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            text_color=("gray10", "gray95"),
            command=self._on_cancel,
        )
        cancel_btn.pack(side="right", padx=(10, 0))

        confirm_btn_color = "#c0392b" if danger else "#2980b9"
        confirm_btn_hover = "#962d22" if danger else "#1f618d"
        confirm_btn = ctk.CTkButton(
            footer,
            text=confirm_text,
            width=140,
            fg_color=confirm_btn_color,
            hover_color=confirm_btn_hover,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_confirm,
        )
        confirm_btn.pack(side="right")

        # Keybindings
        self.bind("<Escape>", lambda _: self._on_cancel())
        if not danger:
            self.bind("<Return>", lambda _: self._on_confirm())

        # Grab focus safely
        self.after(50, self._safe_grab)

    def _safe_grab(self) -> None:
        try:
            if self.winfo_exists():
                self.grab_set()
        except Exception:
            pass

    def _on_confirm(self) -> None:
        self.result = True
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = False
        self.destroy()


class ModernAlertDialog(ctk.CTkToplevel):
    """
    Modern modal alert dialog (Info, Warning, Error) replacing messagebox.showinfo.
    """

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        message: str,
        alert_type: str = "info",
    ) -> None:
        top_parent = parent.winfo_toplevel() if hasattr(parent, "winfo_toplevel") else parent
        super().__init__(top_parent)

        self.title(title)
        self.resizable(False, False)
        self.grid_columnconfigure(0, weight=1)

        try:
            self.transient(top_parent)
        except Exception:
            pass

        # Badge icons and colors
        if alert_type == "error":
            icon_img = get_icon("purge", (24, 24))
            badge_color = ("#fadbd8", "#78281f")
        elif alert_type == "warning":
            icon_img = get_icon("shield", (24, 24))
            badge_color = ("#fdebd0", "#7e5109")
        else:
            icon_img = get_icon("package", (24, 24))
            badge_color = ("#d4e6f1", "#1b4f72")

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 14))
        header.grid_columnconfigure(1, weight=1)

        icon_lbl = ctk.CTkLabel(
            header,
            text="",
            image=icon_img,
            width=46,
            height=46,
            fg_color=badge_color,
            corner_radius=12,
        )
        icon_lbl.grid(row=0, column=0, rowspan=2, padx=(0, 14), sticky="nw")

        title_lbl = ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        title_lbl.grid(row=0, column=1, sticky="w")

        msg_lbl = ctk.CTkLabel(
            header,
            text=message,
            font=ctk.CTkFont(size=13),
            text_color=("gray30", "gray70"),
            wraplength=380,
            justify="left",
            anchor="w",
        )
        msg_lbl.grid(row=1, column=1, sticky="w", pady=(3, 0))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=1, column=0, sticky="ew", padx=24, pady=(6, 18))

        ok_btn = ctk.CTkButton(
            footer,
            text="Dismiss",
            width=100,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.destroy,
        )
        ok_btn.pack(side="right")

        self.bind("<Escape>", lambda _: self.destroy())
        self.bind("<Return>", lambda _: self.destroy())

        self.after(50, self._safe_grab)

    def _safe_grab(self) -> None:
        try:
            if self.winfo_exists():
                self.grab_set()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Convenient functional helpers
# ---------------------------------------------------------------------------

def show_confirm_dialog(
    parent: tk.Misc,
    title: str,
    message: str,
    details: Optional[Sequence[str]] = None,
    items: Optional[Sequence[str]] = None,
    danger: bool = False,
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
) -> bool:
    """
    Display a modal confirmation dialog and block until user responds.
    Returns True if confirmed, False otherwise.
    """
    top_parent = parent.winfo_toplevel() if hasattr(parent, "winfo_toplevel") else parent
    dialog = ModernConfirmDialog(
        parent=top_parent,
        title=title,
        message=message,
        details=details,
        items=items,
        danger=danger,
        confirm_text=confirm_text,
        cancel_text=cancel_text,
    )
    top_parent.wait_window(dialog)
    return dialog.result


def show_alert_dialog(
    parent: tk.Misc,
    title: str,
    message: str,
    alert_type: str = "info",
) -> None:
    """
    Display a modern alert modal dialog and block until dismissed.
    """
    top_parent = parent.winfo_toplevel() if hasattr(parent, "winfo_toplevel") else parent
    dialog = ModernAlertDialog(
        parent=top_parent,
        title=title,
        message=message,
        alert_type=alert_type,
    )
    top_parent.wait_window(dialog)
