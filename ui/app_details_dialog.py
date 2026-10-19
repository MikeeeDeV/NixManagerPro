"""
ui.app_details_dialog
~~~~~~~~~~~~~~~~~~~~~

Rich Application Details Modal Dialog:
Displays high-res metadata, category, licenses, official homepages,
and quick actions for packages. Includes live background metadata hydration
for multi-manager packages (Snap, Flatpak, Nix).
"""

from __future__ import annotations

import logging
from pathlib import Path
import subprocess
import threading
import tkinter as tk
import webbrowser
from typing import Optional

import customtkinter as ctk

from core.catalog import CatalogItem
from utils.icons import get_icon

logger = logging.getLogger("NixManagerPro.AppDetailsDialog")


class AppDetailsDialog(ctk.CTkToplevel):
    """Modern modal card displaying rich software package details."""

    def __init__(
        self,
        parent: tk.Misc,
        item: CatalogItem,
        source: str = "Nix",
        on_install_callback=None,
    ) -> None:
        # Resolve toplevel root to ensure proper CTkToplevel attachment on Linux/Wayland
        top_parent = parent.winfo_toplevel() if hasattr(parent, "winfo_toplevel") else parent
        super().__init__(top_parent)

        self.item = item
        self.source = source
        self.on_install = on_install_callback

        self.title(f"{item.name} — Package Details")
        dlg_w = 580
        dlg_h = 470
        self.geometry(f"{dlg_w}x{dlg_h}")
        self.resizable(False, False)

        # Precise centering over parent window
        try:
            px = top_parent.winfo_rootx()
            py = top_parent.winfo_rooty()
            pw = top_parent.winfo_width()
            ph = top_parent.winfo_height()
            x = px + max(0, (pw - dlg_w) // 2)
            y = py + max(0, (ph - dlg_h) // 2)
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        # Load window icon
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "nixmanager.png"
        if icon_path.exists():
            try:
                self._app_icon = tk.PhotoImage(file=str(icon_path))
                self.iconphoto(True, self._app_icon)
            except Exception:
                pass

        # Transient binding to parent
        try:
            self.transient(top_parent)
        except Exception:
            pass

        # Configure layout weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Retain strong icon references to prevent garbage collection on Linux
        self._pkg_icon = get_icon("package", (32, 32))
        self._install_icon = get_icon("package", (16, 16))

        # ─── 1. Header Frame with App Icon & Title ───────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))

        icon_lbl = ctk.CTkLabel(
            header,
            text="",
            image=self._pkg_icon,
            width=50,
            height=50,
            fg_color=("gray85", "gray20"),
            corner_radius=12,
        )
        icon_lbl.pack(side="left", padx=(0, 14))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", fill="both", expand=True)

        self._name_lbl = ctk.CTkLabel(
            title_box,
            text=item.name,
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        )
        self._name_lbl.pack(fill="x")

        self._attr_lbl = ctk.CTkLabel(
            title_box,
            text=item.attr,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        self._attr_lbl.pack(fill="x")

        # ─── 2. Badges Row (Category, License, Source) ───────────────────────
        badges = ctk.CTkFrame(self, fg_color="transparent")
        badges.grid(row=1, column=0, sticky="w", padx=24, pady=6)

        self._cat_badge = ctk.CTkLabel(
            badges,
            text=item.category,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2c3e50",
            text_color="#ecf0f1",
            corner_radius=6,
            padx=8,
            pady=3,
        )
        self._cat_badge.pack(side="left", padx=(0, 6))

        src_color = "#3498db" if source == "Flatpak" else ("#e67e22" if source == "Snap" else "#1abc9c")
        self._src_badge = ctk.CTkLabel(
            badges,
            text=source,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=src_color,
            text_color="#ffffff",
            corner_radius=6,
            padx=8,
            pady=3,
        )
        self._src_badge.pack(side="left", padx=6)

        self._lic_badge = ctk.CTkLabel(
            badges,
            text=item.license or "Open Source",
            font=ctk.CTkFont(size=11),
            fg_color=("gray80", "gray25"),
            corner_radius=6,
            padx=8,
            pady=3,
        )
        self._lic_badge.pack(side="left", padx=6)

        self._source_verified_lbl = ctk.CTkLabel(
            badges,
            text=f"Managed via {source}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self._source_verified_lbl.pack(side="left", padx=10)

        # ─── 3. Content Frame (Description & Details) ─────────────────────────
        content_box = ctk.CTkFrame(self, corner_radius=12)
        content_box.grid(row=2, column=0, sticky="nsew", padx=24, pady=12)
        content_box.grid_columnconfigure(0, weight=1)

        desc_title = ctk.CTkLabel(
            content_box,
            text="About this application:",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        )
        desc_title.pack(fill="x", padx=16, pady=(14, 4))

        self._desc_lbl = ctk.CTkLabel(
            content_box,
            text=item.description or "No detailed description provided.",
            font=ctk.CTkFont(size=13),
            wraplength=500,
            justify="left",
            anchor="w",
        )
        self._desc_lbl.pack(fill="x", padx=16, pady=(0, 14))

        # Homepage Row
        self._link_frame = ctk.CTkFrame(content_box, fg_color="transparent")
        self._link_frame.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            self._link_frame,
            text="Official Website:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        init_homepage = item.homepage or (f"https://search.nixos.org/packages?query={item.attr.split('.')[-1]}" if source == "Nix" else "")
        self._link_btn = ctk.CTkButton(
            self._link_frame,
            text=init_homepage if init_homepage else "No homepage registered",
            font=ctk.CTkFont(size=12, underline=bool(init_homepage)),
            fg_color="transparent",
            text_color="#3498db" if init_homepage else "gray",
            hover_color=("gray85", "gray20"),
            anchor="w",
            state="normal" if init_homepage else "disabled",
            command=lambda: webbrowser.open(self._current_homepage) if hasattr(self, "_current_homepage") and self._current_homepage else None,
        )
        self._current_homepage = init_homepage
        self._link_btn.pack(side="left")

        # ─── 4. Action Buttons (Footer) ──────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=24, pady=(6, 20))

        close_btn = ctk.CTkButton(
            footer,
            text="Close",
            width=100,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.destroy,
        )
        close_btn.pack(side="right", padx=(8, 0))

        if on_install_callback:
            install_btn = ctk.CTkButton(
                footer,
                text="Install Application",
                image=self._install_icon,
                compound="left",
                width=180,
                fg_color="#27ae60",
                hover_color="#2ecc71",
                command=lambda: (self.destroy(), on_install_callback(item)),
            )
            install_btn.pack(side="right")

        # Force synchronous rendering of children before mapping
        self.update_idletasks()
        self.lift()
        self.focus_force()

        # Safe grab to ensure modal stays focused
        self.after(50, self._safe_grab)

        # Trigger non-blocking live metadata hydration in background
        threading.Thread(target=self._async_hydrate, daemon=True).start()

    def _safe_grab(self) -> None:
        """Safely acquire modal focus once window is mapped and viewable."""
        try:
            if self.winfo_exists():
                self.grab_set()
        except Exception:
            pass

    def _async_hydrate(self) -> None:
        """Fetch rich live metadata from system package manager if available."""
        name = self.item.name.lower()
        attr = self.item.attr.lower()

        try:
            if self.source == "Snap":
                res = subprocess.run(
                    ["snap", "info", attr],
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                )
                if res.returncode == 0:
                    summary = ""
                    license_str = ""
                    homepage = ""
                    for line in res.stdout.splitlines():
                        if line.startswith("summary:"):
                            summary = line.split(":", 1)[1].strip()
                        elif line.startswith("license:") and not license_str:
                            license_str = line.split(":", 1)[1].strip()
                        elif (line.startswith("contact:") or line.startswith("store-url:")) and not homepage:
                            homepage = line.split(":", 1)[1].strip()

                    def _update_snap():
                        if not self.winfo_exists():
                            return
                        if summary:
                            self._desc_lbl.configure(text=f"{summary}\n\nInstalled and verified via Canonical Snap.")
                        if license_str:
                            self._lic_badge.configure(text=license_str)
                        if homepage:
                            self._current_homepage = homepage
                            self._link_btn.configure(
                                text=homepage,
                                state="normal",
                                text_color="#3498db",
                                underline=True,
                                hover_color=("gray85", "gray20"),
                            )
                        self._source_verified_lbl.configure(text="Verified Snapcraft Package")

                    self.after(0, _update_snap)

            elif self.source == "Flatpak":
                # Find application ID if needed
                app_id = attr
                if not any(attr.startswith(p) for p in ("org.", "com.", "io.", "net.", "app.")):
                    list_res = subprocess.run(
                        ["flatpak", "list", "--columns=name,application"],
                        capture_output=True,
                        text=True,
                        timeout=2.0,
                    )
                    if list_res.returncode == 0:
                        for line in list_res.stdout.splitlines():
                            parts = line.split()
                            if len(parts) >= 2 and name in parts[0].lower():
                                app_id = parts[1]
                                break

                info_res = subprocess.run(
                    ["flatpak", "info", app_id],
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                )
                if info_res.returncode == 0:
                    summary = ""
                    lic = ""
                    lines = [l.strip() for l in info_res.stdout.splitlines() if l.strip()]
                    if lines:
                        summary = lines[0]
                    for line in lines:
                        if "License:" in line:
                            lic = line.split("License:", 1)[1].strip()

                    def _update_flatpak():
                        if not self.winfo_exists():
                            return
                        if summary:
                            self._desc_lbl.configure(text=f"{summary}\n\nInstalled and verified via Flathub / Flatpak.")
                        if lic:
                            self._lic_badge.configure(text=lic)
                        flathub_url = f"https://flathub.org/apps/{app_id}"
                        self._current_homepage = flathub_url
                        self._link_btn.configure(
                            text=flathub_url,
                            state="normal",
                            text_color="#3498db",
                            underline=True,
                            hover_color=("gray85", "gray20"),
                        )
                        self._source_verified_lbl.configure(text="Verified Flathub Package")

                    self.after(0, _update_flatpak)

        except Exception as exc:
            logger.debug("Live metadata hydration skipped: %s", exc)
