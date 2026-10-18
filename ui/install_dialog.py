"""
ui.install_dialog
~~~~~~~~~~~~~~~~~

Practical, fast package discovery and installation interface.
Features:
- Instant curated catalog with categories and descriptions (0ms latency)
- Real-time search filtering
- Upstream Nixpkgs fallback search
- Embedded live installation terminal so users see downloading progress in-tab!
"""

from __future__ import annotations

import asyncio
import logging
import webbrowser
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, TYPE_CHECKING


import customtkinter as ctk

from core.catalog import CURATED_PACKAGES, CatalogItem, search_catalog
from utils.notifications import DesktopNotifier

if TYPE_CHECKING:
    from core.package_manager import NixPackageManager
    from utils.worker import WorkerPool


class InstallDialog(ctk.CTkFrame):
    """Practical App-Store style package installer with embedded live log console."""

    def __init__(
        self,
        master: tk.Misc,
        pkg_manager: NixPackageManager,
        worker: WorkerPool,
        logger: logging.Logger,
        console_cb=None,
    ) -> None:
        super().__init__(master)
        self._pm = pkg_manager
        self._worker = worker
        self._log = logger
        self._console_cb = console_cb

        self._active_items: List[CatalogItem | Dict[str, str]] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ---- search & category bar -----------------------------------------
        top_bar = ctk.CTkFrame(self)
        top_bar.grid(row=0, column=0, sticky="ew", padx=6, pady=(0, 6))

        # Category filter
        categories = ["All", "Developer Tools", "System & Shell", "Runtimes", "Networking", "Media", "Utilities"]
        self._category_var = tk.StringVar(value="All")
        self._cat_menu = ctk.CTkOptionMenu(
            top_bar,
            values=categories,
            variable=self._category_var,
            width=150,
            command=lambda _v: self._on_filter(),
        )
        self._cat_menu.pack(side="left", padx=8, pady=8)

        # Search field
        self._query_var = tk.StringVar()
        self._query_var.trace_add("write", lambda *args: self._on_filter())

        self._entry = ctk.CTkEntry(
            top_bar,
            textvariable=self._query_var,
            placeholder_text="Search packages (e.g. git, htop, neovim, python, ripgrep)...",
            height=36,
        )
        self._entry.pack(side="left", padx=6, pady=8, fill="x", expand=True)

        upstream_btn = ctk.CTkButton(
            top_bar,
            text="🌐 Upstream Nixpkgs",
            width=160,
            command=self._on_search_upstream,
        )
        upstream_btn.pack(side="right", padx=8, pady=8)

        # ---- status line ---------------------------------------------------
        self._status = ctk.CTkLabel(
            self,
            text="Select a package from the curated catalog or search above to install.",
            font=ctk.CTkFont(size=12),
        )
        self._status.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 4))

        # ---- packages treeview ---------------------------------------------
        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=6, pady=2)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure(
            "Store.Treeview",
            background="#16213e",
            foreground="#e0e0e0",
            fieldbackground="#16213e",
            rowheight=32,
            font=("Segoe UI", 11),
        )
        style.configure(
            "Store.Treeview.Heading",
            background="#0f3460",
            foreground="#ffffff",
            font=("Segoe UI", 11, "bold"),
        )
        style.map("Store.Treeview", background=[("selected", "#1f4068")])

        self._tree = ttk.Treeview(
            tree_frame,
            columns=("name", "category", "attr", "desc"),
            show="headings",
            style="Store.Treeview",
            selectmode="browse",
        )
        self._tree.heading("name", text="Package")
        self._tree.heading("category", text="Category")
        self._tree.heading("attr", text="Attribute Path")
        self._tree.heading("desc", text="Description")

        self._tree.column("name", width=140, anchor="w")
        self._tree.column("category", width=130, anchor="center")
        self._tree.column("attr", width=160, anchor="w")
        self._tree.column("desc", width=420, anchor="w")

        self._tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # ---- WingetUI-style Package Details Card & Action Bar -------------
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.grid(row=3, column=0, sticky="ew", padx=6, pady=(4, 6))
        bottom_frame.grid_columnconfigure(0, weight=1)

        # Details Card Container
        self._card = ctk.CTkFrame(bottom_frame, corner_radius=8, fg_color=("gray85", "#131b2e"))
        self._card.grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 4))
        self._card.grid_columnconfigure(1, weight=1)

        # Left column of card: Title & Badges
        card_left = ctk.CTkFrame(self._card, fg_color="transparent")
        card_left.grid(row=0, column=0, padx=12, pady=8, sticky="nw")

        self._card_title = ctk.CTkLabel(
            card_left,
            text="Select any package above",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        )
        self._card_title.pack(anchor="w")

        self._card_attr = ctk.CTkLabel(
            card_left,
            text="Attribute: –",
            font=ctk.CTkFont(size=11),
            text_color="#8ab4f8",
            anchor="w",
        )
        self._card_attr.pack(anchor="w")

        # Right column of card: Description, Badges & Actions
        card_right = ctk.CTkFrame(self._card, fg_color="transparent")
        card_right.grid(row=0, column=1, padx=12, pady=8, sticky="ew")

        self._card_desc = ctk.CTkLabel(
            card_right,
            text="Click a package to see detailed description, license, and homepage link.",
            font=ctk.CTkFont(size=12),
            wraplength=480,
            justify="left",
            anchor="w",
        )
        self._card_desc.pack(anchor="w", pady=(0, 4))

        meta_row = ctk.CTkFrame(card_right, fg_color="transparent")
        meta_row.pack(anchor="w")

        self._card_meta = ctk.CTkLabel(
            meta_row,
            text="Source: nixpkgs",
            font=ctk.CTkFont(size=11),
            text_color="#a0a0a0",
        )
        self._card_meta.pack(side="left", padx=(0, 10))

        self._homepage_btn = ctk.CTkButton(
            meta_row,
            text="🌐 Homepage ↗",
            width=110,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color="#3498db",
            hover_color=("gray75", "gray25"),
            state="disabled",
            command=self._open_homepage,
        )
        self._homepage_btn.pack(side="left", padx=4)

        copy_cmd_btn = ctk.CTkButton(
            meta_row,
            text="📋 Copy Command",
            width=120,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color="#a3d9a5",
            hover_color=("gray75", "gray25"),
            command=self._copy_command,
        )
        copy_cmd_btn.pack(side="left", padx=4)

        # Action Button
        self._install_btn = ctk.CTkButton(
            self._card,
            text="⬇  Install Package",
            width=180,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#27ae60",
            hover_color="#2ecc71",
            command=self._on_install,
        )
        self._install_btn.grid(row=0, column=2, padx=14, pady=8, sticky="e")

        # Mini live terminal inside the tab so user SEES output directly
        self._mini_log = tk.Text(
            bottom_frame,
            height=4,
            state="disabled",
            bg="#111726",
            fg="#9bc53d",
            font=("Consolas", 10),
            relief="flat",
            padx=6,
            pady=4,
        )
        self._mini_log.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 4))


        # Populate with curated catalog initially
        self._on_filter()

    # ---- filtering & display -----------------------------------------------

    def _on_filter(self) -> None:
        query = self._query_var.get().strip()
        cat = self._category_var.get()
        items = search_catalog(query, cat)
        self._populate_items(items)

    def _populate_items(self, items: List[CatalogItem]) -> None:
        self._active_items = items
        self._tree.delete(*self._tree.get_children())
        for idx, it in enumerate(items):
            self._tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(it.name, it.category, it.attr, it.description),
            )
        self._status.configure(text=f"Showing {len(items)} popular curated package(s)")

    def _on_tree_select(self, _event=None) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if idx >= len(self._active_items):
            return

        item = self._active_items[idx]
        name = item.name if isinstance(item, CatalogItem) else item.get("name", "")
        attr = item.attr if isinstance(item, CatalogItem) else item.get("attr", "")
        desc = item.description if isinstance(item, CatalogItem) else "Upstream package derivation"
        license_str = getattr(item, "license", "Open Source")
        homepage = getattr(item, "homepage", "")

        self._card_title.configure(text=name)
        self._card_attr.configure(text=f"Attribute: {attr}")
        self._card_desc.configure(text=desc)
        self._card_meta.configure(text=f"License: {license_str}  |  Source: nixpkgs")

        self._current_homepage = homepage
        if homepage:
            self._homepage_btn.configure(state="normal")
        else:
            self._homepage_btn.configure(state="disabled")

        self._current_attr = attr

    def _open_homepage(self) -> None:
        url = getattr(self, "_current_homepage", "")
        if url:
            webbrowser.open(url)

    def _copy_command(self) -> None:
        attr = getattr(self, "_current_attr", "")
        if not attr:
            sel = self._tree.selection()
            if sel:
                idx = int(sel[0])
                it = self._active_items[idx]
                attr = it.attr if isinstance(it, CatalogItem) else it.get("attr", "")

        if attr:
            cmd = f"nix-env -iA {attr}"
            self.clipboard_clear()
            self.clipboard_append(cmd)
            self._status.configure(text=f"📋 Copied to clipboard: {cmd}")

    # ---- upstream nixpkgs search fallback ----------------------------------


    def _on_search_upstream(self) -> None:
        query = self._query_var.get().strip()
        if not query:
            self._status.configure(text="Please type a package name to search upstream Nixpkgs.")
            return

        self._status.configure(text=f"Evaluating Nixpkgs for '{query}' (may take a moment)...")
        self._log_terminal(f"Searching Nixpkgs for '{query}'...")
        self._worker.submit(self._search_upstream_bg, query)

    def _search_upstream_bg(self, query: str) -> None:
        try:
            results = asyncio.run(self._pm.search(query))
        except Exception as exc:
            self._log.error("Upstream search failed: %s", exc)
            results = []
        self.after(0, self._populate_upstream, query, results)

    def _populate_upstream(self, query: str, results: List[Dict[str, str]]) -> None:
        self._active_items = results
        self._tree.delete(*self._tree.get_children())
        for idx, hit in enumerate(results):
            self._tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(hit.get("name", ""), "Nixpkgs", hit.get("attr", ""), "Upstream Derivation"),
            )
        self._status.configure(text=f"Found {len(results)} upstream result(s) for '{query}'")

    # ---- installation ------------------------------------------------------

    def _on_install(self) -> None:
        sel = self._tree.selection()
        if not sel:
            self._status.configure(text="⚠️ Please click and select a package from the table first.")
            return

        idx = int(sel[0])
        item = self._active_items[idx]

        attr = item.attr if isinstance(item, CatalogItem) else item.get("attr", "")
        pkg_name = item.name if isinstance(item, CatalogItem) else item.get("name", attr)

        self._log.info("Starting installation of %s (%s)", pkg_name, attr)
        self._status.configure(text=f"⏳ Installing {pkg_name}... check progress below.")
        self._install_btn.configure(state="disabled")

        self._clear_mini_log()
        self._log_terminal(f"Starting installation of {attr}...")

        self._worker.submit(self._install_bg, attr, pkg_name)

    def _install_bg(self, attr: str, pkg_name: str) -> None:
        # Hook local mini-log
        orig_cb = self._pm._exec._on_output

        def custom_cb(stream, line):
            if orig_cb:
                orig_cb(stream, line)
            self.after(0, self._log_terminal, line)

        self._pm._exec.set_output_callback(custom_cb)

        try:
            asyncio.run(self._pm.install(attr))
            msg = f"✓ Successfully installed {pkg_name}!"
            urgency = "normal"
        except Exception as exc:
            msg = f"✗ Failed installing {pkg_name}: {exc}"
            urgency = "critical"
            self._log.error(msg)
        finally:
            self._pm._exec.set_output_callback(orig_cb)

        DesktopNotifier.send("NixManager Pro", msg, urgency=urgency)
        self.after(0, self._install_finished, msg)

    def _install_finished(self, msg: str) -> None:
        self._status.configure(text=msg)
        self._install_btn.configure(state="normal")
        self._log_terminal(f"\n{msg}\n")

    # ---- mini-log helpers --------------------------------------------------

    def _log_terminal(self, text: str) -> None:
        self._mini_log.configure(state="normal")
        self._mini_log.insert("end", f"{text}\n")
        self._mini_log.configure(state="disabled")
        self._mini_log.see("end")

    def _clear_mini_log(self) -> None:
        self._mini_log.configure(state="normal")
        self._mini_log.delete("1.0", "end")
        self._mini_log.configure(state="disabled")
