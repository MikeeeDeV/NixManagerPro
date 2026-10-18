"""
ui.app_details_dialog
~~~~~~~~~~~~~~~~~~~~~

Rich Application Details Modal Dialog:
Displays high-res metadata, category, licenses, official homepages,
and quick actions for packages.
"""

from __future__ import annotations

import tkinter as tk
import webbrowser
from typing import Optional

import customtkinter as ctk

from core.catalog import CatalogItem


class AppDetailsDialog(ctk.CTkToplevel):
    """Modern modal card displaying rich software package details."""

    def __init__(
        self,
        parent: tk.Misc,
        item: CatalogItem,
        source: str = "Nix",
        on_install_callback=None,
    ) -> None:
        super().__init__(parent)
        self.title(f"{item.name} — Package Details")
        self.geometry("540x460")
        self.resizable(False, False)

        # Center dialog relative to parent
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header Frame with App Icon & Title
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))

        # Icon
        icon_lbl = ctk.CTkLabel(
            header,
            text="📦",
            font=ctk.CTkFont(size=36),
            width=50,
            height=50,
            fg_color=("gray85", "gray20"),
            corner_radius=12,
        )
        icon_lbl.pack(side="left", padx=(0, 14))

        # Title & Attr
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", fill="both", expand=True)

        name_lbl = ctk.CTkLabel(
            title_box,
            text=item.name,
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        )
        name_lbl.pack(fill="x")

        attr_lbl = ctk.CTkLabel(
            title_box,
            text=item.attr,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        attr_lbl.pack(fill="x")

        # 2. Badges Row (Category, License, Source)
        badges = ctk.CTkFrame(self, fg_color="transparent")
        badges.grid(row=1, column=0, sticky="w", padx=24, pady=6)

        # Category Badge
        cat_badge = ctk.CTkLabel(
            badges,
            text=f"📁 {item.category}",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2c3e50",
            text_color="#ecf0f1",
            corner_radius=6,
            padx=8,
            pady=3,
        )
        cat_badge.pack(side="left", padx=(0, 6))

        # Source Badge
        src_color = "#3498db" if source == "Flatpak" else ("#e67e22" if source == "Snap" else "#1abc9c")
        src_badge = ctk.CTkLabel(
            badges,
            text=f"⚡ {source}",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=src_color,
            text_color="#ffffff",
            corner_radius=6,
            padx=8,
            pady=3,
        )
        src_badge.pack(side="left", padx=6)

        # License Badge
        lic_badge = ctk.CTkLabel(
            badges,
            text=f"⚖️ {item.license or 'Open Source'}",
            font=ctk.CTkFont(size=11),
            fg_color=("gray80", "gray25"),
            corner_radius=6,
            padx=8,
            pady=3,
        )
        lic_badge.pack(side="left", padx=6)

        # 3. Content Frame (Description & Details)
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

        desc_lbl = ctk.CTkLabel(
            content_box,
            text=item.description or "No detailed description provided.",
            font=ctk.CTkFont(size=13),
            wraplength=460,
            justify="left",
            anchor="w",
        )
        desc_lbl.pack(fill="x", padx=16, pady=(0, 14))

        # Homepage Row
        if item.homepage:
            link_frame = ctk.CTkFrame(content_box, fg_color="transparent")
            link_frame.pack(fill="x", padx=16, pady=(0, 12))

            ctk.CTkLabel(
                link_frame,
                text="Official Website:",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(side="left", padx=(0, 8))

            link_btn = ctk.CTkButton(
                link_frame,
                text=f"🌐 {item.homepage}",
                font=ctk.CTkFont(size=12, underline=True),
                fg_color="transparent",
                text_color="#3498db",
                hover_color=("gray85", "gray20"),
                anchor="w",
                command=lambda: webbrowser.open(item.homepage),
            )
            link_btn.pack(side="left")

        # 4. Action Buttons (Footer)
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
                text="⚡ Install This Application",
                width=180,
                fg_color="#27ae60",
                hover_color="#2ecc71",
                command=lambda: (self.destroy(), on_install_callback(item)),
            )
            install_btn.pack(side="right")
