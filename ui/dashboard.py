"""
ui.dashboard
~~~~~~~~~~~~~

Top‑level dashboard tab showing:

* Nix daemon status indicator
* Store disk usage
* Channel information
* Quick‑action buttons (Refresh, Garbage Collect)
* Embedded :class:`~ui.package_table.PackageTable`
"""

from __future__ import annotations

import asyncio
import logging
import tkinter as tk
from typing import TYPE_CHECKING

import customtkinter as ctk

from utils.notifications import DesktopNotifier
from .package_table import PackageTable


if TYPE_CHECKING:
    from core.diagnostics import Diagnostics
    from core.package_manager import NixPackageManager
    from utils.worker import WorkerPool


class Dashboard(ctk.CTkFrame):
    """Primary view — health overview + installed packages."""

    def __init__(
        self,
        master: tk.Misc,
        pkg_manager: NixPackageManager,
        diagnostics: Diagnostics,
        worker: WorkerPool,
        logger: logging.Logger,
        console_cb=None,
    ) -> None:
        super().__init__(master)
        self._pm = pkg_manager
        self._diag = diagnostics
        self._worker = worker
        self._log = logger
        self._console_cb = console_cb

        # ---- layout -------------------------------------------------------
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)          # table gets all extra space

        # ---- status cards --------------------------------------------------
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 2))
        status_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Card 1 – daemon
        self._daemon_card = self._make_card(status_frame, "Daemon", "…", col=0)
        # Card 2 – store usage
        self._store_card = self._make_card(status_frame, "Store Size", "…", col=1)
        # Card 3 – channels
        self._channel_card = self._make_card(status_frame, "Channels", "…", col=2)

        # ---- action buttons ------------------------------------------------
        btn_frame = ctk.CTkFrame(self, height=44)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=6, pady=4)

        ctk.CTkButton(
            btn_frame, text="⟳  Refresh All", width=140, command=self.refresh_all,
        ).pack(side="left", padx=8, pady=6)

        ctk.CTkButton(
            btn_frame, text="🧹  Garbage Collect", width=160,
            fg_color="#e67e22", hover_color="#f39c12",
            command=self._run_gc,
        ).pack(side="left", padx=4, pady=6)

        # ---- package table -------------------------------------------------
        self.pkg_table = PackageTable(
            master=self,
            pkg_manager=pkg_manager,
            worker=worker,
            logger=logger,
            console_cb=console_cb,
        )
        self.pkg_table.grid(row=2, column=0, sticky="nsew", padx=6, pady=(2, 6))

    # ---- card factory -----------------------------------------------------

    @staticmethod
    def _make_card(parent: tk.Misc, title: str, value: str, col: int) -> ctk.CTkLabel:
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=0, column=col, sticky="ew", padx=6, pady=6)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text=title,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#8ab4f8",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))

        value_lbl = ctk.CTkLabel(
            card, text=value,
            font=ctk.CTkFont(size=14),
        )
        value_lbl.grid(row=1, column=0, sticky="w", padx=12, pady=(2, 10))
        return value_lbl

    # ---- public API -------------------------------------------------------

    def refresh_all(self) -> None:
        """Kick off background refresh of status cards + package table."""
        self._log.info("Dashboard: refresh requested")
        self._worker.submit(self._fetch_status)
        self.pkg_table.refresh()

    # ---- background helpers -----------------------------------------------

    def _fetch_status(self) -> None:
        try:
            daemon = asyncio.run(self._diag.daemon_status())
            store  = asyncio.run(self._diag.store_usage())
            chans  = asyncio.run(self._diag.channel_list())
        except Exception as exc:
            self._log.error("Status fetch failed: %s", exc)
            daemon = store = chans = None
        self.after(0, self._update_cards, daemon, store, chans)

    def _update_cards(self, daemon, store, chans) -> None:
        if daemon is not None:
            icon = "🟢" if daemon.active else "🔴"
            self._daemon_card.configure(text=f"{icon}  {daemon.status_text}")
        else:
            self._daemon_card.configure(text="⚠  error")

        if store is not None:
            self._store_card.configure(text=store.size_human)
        else:
            self._store_card.configure(text="N/A")

        if chans is not None:
            self._channel_card.configure(text=chans[:80])   # truncate long output
        else:
            self._channel_card.configure(text="N/A")

    # ---- garbage collection -----------------------------------------------

    def _run_gc(self) -> None:
        self._log.info("User requested garbage collection")
        if self._console_cb:
            self._console_cb("info", "Starting nix-store --gc …")
        self._worker.submit(self._gc_background)

    def _gc_background(self) -> None:
        try:
            summary = asyncio.run(self._pm.garbage_collect())
            msg = f"✓ GC complete. {summary.strip()}"
        except Exception as exc:
            msg = f"✗ GC failed: {exc}"
            self._log.error(msg)

        if self._console_cb:
            self._console_cb("info", msg)

        DesktopNotifier.send("Nix Garbage Collection", msg)
        # Refresh the store‑size card
        self.after(500, self.refresh_all)

