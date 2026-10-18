"""
ui.install_dialog
~~~~~~~~~~~~~~~~~

Search + install interface.  The user types a query, background‑searches
``nix-env -qaP``, picks a result, and installs it — all non‑blocking.
"""

from __future__ import annotations

import asyncio
import logging
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, TYPE_CHECKING

import customtkinter as ctk

from utils.notifications import DesktopNotifier


if TYPE_CHECKING:
    from core.package_manager import NixPackageManager
    from utils.worker import WorkerPool


class InstallDialog(ctk.CTkFrame):
    """Search‑and‑install panel embedded in its own tab."""

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

        self._results: List[Dict[str, str]] = []

        # ---- layout -------------------------------------------------------
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ---- search bar ---------------------------------------------------
        search_frame = ctk.CTkFrame(self, height=50)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self._query_var = tk.StringVar()
        self._entry = ctk.CTkEntry(
            search_frame,
            textvariable=self._query_var,
            placeholder_text="Search packages (e.g. htop, vim, nodejs)…",
            width=500,
            height=36,
        )
        self._entry.pack(side="left", padx=10, pady=8, fill="x", expand=True)
        self._entry.bind("<Return>", lambda _e: self._on_search())

        self._search_btn = ctk.CTkButton(
            search_frame, text="🔍  Search", width=110, command=self._on_search,
        )
        self._search_btn.pack(side="left", padx=(0, 6), pady=8)

        # ---- status label -------------------------------------------------
        self._status = ctk.CTkLabel(self, text="Enter a query above to search the Nix store.")
        self._status.grid(row=1, column=0, sticky="w", padx=10)

        # ---- results treeview ---------------------------------------------
        style = ttk.Style()
        style.configure(
            "Search.Treeview",
            background="#16213e",
            foreground="#e0e0e0",
            fieldbackground="#16213e",
            rowheight=28,
            font=("Segoe UI", 11),
        )
        style.configure(
            "Search.Treeview.Heading",
            background="#0f3460",
            foreground="#ffffff",
            font=("Segoe UI", 11, "bold"),
        )
        style.map("Search.Treeview", background=[("selected", "#1a1a5e")])

        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=2, column=0, sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(
            tree_frame,
            columns=("attr", "name"),
            show="headings",
            style="Search.Treeview",
            selectmode="browse",
        )
        self._tree.heading("attr", text="Attribute Path")
        self._tree.heading("name", text="Package")
        self._tree.column("attr", width=360, anchor="w")
        self._tree.column("name", width=300, anchor="w")
        self._tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self._tree.configure(yscrollcommand=vsb.set)

        # ---- install button ------------------------------------------------
        btn_frame = ctk.CTkFrame(self, height=44)
        btn_frame.grid(row=3, column=0, sticky="ew", pady=(6, 0))

        self._install_btn = ctk.CTkButton(
            btn_frame,
            text="⬇  Install Selected",
            width=180,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            command=self._on_install,
        )
        self._install_btn.pack(side="right", padx=10, pady=6)

    # ---- search -----------------------------------------------------------

    def _on_search(self) -> None:
        query = self._query_var.get().strip()
        if not query:
            return
        self._status.configure(text=f"Searching for '{query}'...")
        self._search_btn.configure(state="disabled")
        self._worker.submit(self._search_background, query)

    def _search_background(self, query: str) -> None:
        try:
            results = asyncio.run(self._pm.search(query))
        except Exception as exc:
            self._log.error("Search failed: %s", exc)
            results = []
        self.after(0, self._populate_results, query, results)

    def _populate_results(self, query: str, results: List[Dict[str, str]]) -> None:
        self._results = results
        self._tree.delete(*self._tree.get_children())
        for idx, hit in enumerate(results):
            self._tree.insert("", "end", iid=str(idx), values=(hit["attr"], hit["name"]))
        self._status.configure(text=f"{len(results)} result(s) for '{query}'")
        self._search_btn.configure(state="normal")

    # ---- install ----------------------------------------------------------

    def _on_install(self) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        hit = self._results[idx]
        attr = hit["attr"]
        self._log.info("User requested install: %s", attr)
        self._status.configure(text=f"Installing {attr}…")
        self._install_btn.configure(state="disabled")
        self._worker.submit(self._install_background, attr)

    def _install_background(self, attr: str) -> None:
        try:
            asyncio.run(self._pm.install(attr))
            msg = f"✓ Installed {attr}"
        except Exception as exc:
            msg = f"✗ Install failed for {attr}: {exc}"
            self._log.error(msg)

        if self._console_cb:
            self._console_cb("info", msg)

        DesktopNotifier.send("Nix Package Manager", msg)
        self.after(0, self._install_done, msg)


    def _install_done(self, msg: str) -> None:
        self._status.configure(text=msg)
        self._install_btn.configure(state="normal")
