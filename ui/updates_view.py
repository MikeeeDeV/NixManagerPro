"""
ui.updates_view
~~~~~~~~~~~~~~~

Dedicated WingetUI-style Updates Center:
- Scans for updates across Nix channels, Snap, and Flatpak.
- Lists outdated packages with current vs new version comparison.
- Provides '⚡ Check for Updates', '🚀 Upgrade Selected', and '✨ Upgrade All'.
"""

from __future__ import annotations

import asyncio
import logging
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, List, Dict

import customtkinter as ctk

from utils.notifications import DesktopNotifier

if TYPE_CHECKING:
    from core.package_manager import NixPackageManager, UpdateCandidate
    from utils.worker import WorkerPool


class UpdatesView(ctk.CTkFrame):
    """Unified Updates Tab with batch upgrading capabilities."""

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
        self._candidates: List[UpdateCandidate] = []
        self._item_map: Dict[str, UpdateCandidate] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header & Summary Banner
        self._header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))

        self._title_lbl = ctk.CTkLabel(
            self._header_frame,
            text="🔄 Updates Center",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self._title_lbl.pack(side="left")

        self._status_badge = ctk.CTkLabel(
            self._header_frame,
            text="Ready to check",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#34495e",
            text_color="#ecf0f1",
            corner_radius=8,
            padx=10,
            pady=4,
        )
        self._status_badge.pack(side="left", padx=14)

        # 2. Action Toolbar
        toolbar = ctk.CTkFrame(self, height=48, corner_radius=10)
        toolbar.grid(row=1, column=0, sticky="ew", padx=16, pady=6)

        self._btn_check = ctk.CTkButton(
            toolbar,
            text="⚡ Check for Updates",
            width=150,
            command=self.check_for_updates,
        )
        self._btn_check.pack(side="left", padx=8, pady=8)

        self._btn_upgrade_selected = ctk.CTkButton(
            toolbar,
            text="🚀 Upgrade Selected",
            width=150,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            command=self.upgrade_selected,
        )
        self._btn_upgrade_selected.pack(side="left", padx=6, pady=8)

        self._btn_upgrade_all = ctk.CTkButton(
            toolbar,
            text="✨ Upgrade All",
            width=140,
            fg_color="#8e44ad",
            hover_color="#9b59b6",
            command=self.upgrade_all,
        )
        self._btn_upgrade_all.pack(side="left", padx=6, pady=8)

        # 3. Updates Table
        table_container = ctk.CTkFrame(self, corner_radius=10)
        table_container.grid(row=2, column=0, sticky="nsew", padx=16, pady=(6, 14))
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(0, weight=1)

        cols = ("name", "cur_ver", "new_ver", "manager")
        self._tree = ttk.Treeview(
            table_container,
            columns=cols,
            show="headings",
            selectmode="extended",
        )
        self._tree.heading("name", text="Application Name")
        self._tree.heading("cur_ver", text="Installed Version")
        self._tree.heading("new_ver", text="Available Version")
        self._tree.heading("manager", text="Source / Manager")

        self._tree.column("name", width=220, anchor="w")
        self._tree.column("cur_ver", width=140, anchor="center")
        self._tree.column("new_ver", width=140, anchor="center")
        self._tree.column("manager", width=120, anchor="center")

        scroll = ttk.Scrollbar(table_container, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)

        self._tree.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=6)
        scroll.grid(row=0, column=1, sticky="ns", padx=(0, 6), pady=6)

    def _log_console(self, text: str) -> None:
        if self._console_cb:
            self._console_cb("stdout", f"[Updates] {text}")

    def check_for_updates(self) -> None:
        """Scan for available upgrades."""
        self._btn_check.configure(state="disabled", text="⏳ Scanning...")
        self._status_badge.configure(text="Checking repositories...", fg_color="#f39c12")
        self._log_console("Scanning Nix, Snap, and Flatpak repositories for updates...")

        async def _scan():
            return await self._pm.check_updates()

        def _on_done(candidates: List[UpdateCandidate]):
            self._candidates = candidates
            self._tree.delete(*self._tree.get_children())
            self._item_map.clear()

            for cand in candidates:
                item_id = self._tree.insert(
                    "",
                    "end",
                    values=(
                        cand.name,
                        cand.current_version,
                        f"⬆ {cand.new_version}",
                        f"📦 {cand.source}",
                    ),
                )
                self._item_map[item_id] = cand

            count = len(candidates)
            if count > 0:
                self._status_badge.configure(
                    text=f"🔔 {count} Update(s) Available", fg_color="#27ae60"
                )
                self._log_console(f"Found {count} available update(s)!")
                DesktopNotifier.info("Updates Available", f"{count} application update(s) ready to install.")
            else:
                self._status_badge.configure(
                    text="✓ All software up to date", fg_color="#2980b9"
                )
                self._log_console("All applications across Nix, Snap, and Flatpak are up to date.")

            self._btn_check.configure(state="normal", text="⚡ Check for Updates")

        def _on_err(exc: Exception):
            self._status_badge.configure(text="Error checking", fg_color="#c0392b")
            self._log_console(f"Error checking updates: {exc}")
            self._btn_check.configure(state="normal", text="⚡ Check for Updates")

        self._worker.submit_async(_scan, on_success=_on_done, on_error=_on_err)

    def refresh_all(self) -> None:
        """Alias for app startup refresh."""
        self.check_for_updates()

    def upgrade_selected(self) -> None:
        """Upgrade packages selected in tree."""
        selected_ids = self._tree.selection()
        if not selected_ids:
            DesktopNotifier.warn("No selection", "Please select at least one application to upgrade.")
            return

        candidates = [self._item_map[iid] for iid in selected_ids if iid in self._item_map]
        self._run_batch_upgrade(candidates)

    def upgrade_all(self) -> None:
        """Upgrade all candidates."""
        if not self._candidates:
            # Run generic upgrade across all managers
            self._btn_upgrade_all.configure(state="disabled", text="⏳ Upgrading All...")
            self._status_badge.configure(text="Upgrading entire system...", fg_color="#8e44ad")
            self._log_console("Starting full-system upgrade across Nix, Snap, and Flatpak...")

            async def _run():
                return await self._pm.upgrade_all_generic()

            def _done(out):
                self._log_console("Full-system upgrade completed successfully!")
                self._log_console(out)
                self._status_badge.configure(text="✓ Upgrade finished", fg_color="#27ae60")
                self._btn_upgrade_all.configure(state="normal", text="✨ Upgrade All")
                self.check_for_updates()

            def _err(e):
                self._log_console(f"Upgrade error: {e}")
                self._status_badge.configure(text="Upgrade failed", fg_color="#c0392b")
                self._btn_upgrade_all.configure(state="normal", text="✨ Upgrade All")

            self._worker.submit_async(_run, on_success=_done, on_error=_err)
            return

        self._run_batch_upgrade(list(self._candidates))

    def _run_batch_upgrade(self, candidates: List[UpdateCandidate]) -> None:
        total = len(candidates)
        self._btn_upgrade_selected.configure(state="disabled")
        self._btn_upgrade_all.configure(state="disabled")
        self._status_badge.configure(text=f"Upgrading {total} app(s)...", fg_color="#e67e22")

        async def _upgrade_batch():
            results = []
            for i, cand in enumerate(candidates, start=1):
                self._log_console(f"[{i}/{total}] Upgrading {cand.source} package: {cand.name}...")
                try:
                    res = await self._pm.upgrade_candidate(cand)
                    results.append(f"✓ {cand.name}: {res}")
                except Exception as e:
                    results.append(f"✗ {cand.name}: {e}")
            return results

        def _on_done(results):
            for r in results:
                self._log_console(r)
            self._status_badge.configure(text="✓ Upgrades completed", fg_color="#27ae60")
            self._btn_upgrade_selected.configure(state="normal")
            self._btn_upgrade_all.configure(state="normal")
            DesktopNotifier.info("Upgrade Complete", f"Successfully processed {total} package upgrade(s).")
            self.check_for_updates()

        def _on_err(exc):
            self._log_console(f"Batch upgrade failure: {exc}")
            self._status_badge.configure(text="Upgrade errors", fg_color="#c0392b")
            self._btn_upgrade_selected.configure(state="normal")
            self._btn_upgrade_all.configure(state="normal")

        self._worker.submit_async(_upgrade_batch, on_success=_on_done, on_error=_on_err)
