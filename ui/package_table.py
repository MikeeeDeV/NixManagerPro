"""
ui.package_table
~~~~~~~~~~~~~~~~

Treeview‑based table that lists all installed Nix packages.  Supports:

* Refresh (background‑fetches ``nix-env -q``)
* Right‑click → Uninstall
* Name column heading
* Version column heading
"""

from __future__ import annotations

import asyncio
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING, List

import customtkinter as ctk

from core.catalog import resolve_rich_details
from core.exporter import NixEnvironmentExporter
from utils.icons import get_icon
from utils.notifications import DesktopNotifier
from .app_details_dialog import AppDetailsDialog
from .modern_dialog import show_alert_dialog, show_confirm_dialog


if TYPE_CHECKING:
    from core.package_manager import NixPackageManager, PackageInfo
    from utils.worker import WorkerPool


class PackageTable(ctk.CTkFrame):
    """Scrollable table of installed packages."""

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
        self._console_cb = console_cb      # optional (stream, line) callback
        self._cached_packages: List[PackageInfo] = []

        # ---- layout -------------------------------------------------------
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ---- toolbar -------------------------------------------------------
        toolbar = ctk.CTkFrame(self, height=44)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        self._count_lbl = ctk.CTkLabel(
            toolbar,
            text="Packages: –",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self._count_lbl.pack(side="left", padx=10)

        # Search bar
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter())
        self._search_entry = ctk.CTkEntry(
            toolbar,
            textvariable=self._search_var,
            placeholder_text="Filter installed packages...",
            width=200,
            height=28,
        )
        self._search_entry.pack(side="left", padx=6, pady=4)

        # Source filter
        self._source_filter_var = tk.StringVar(value="All Sources")
        self._source_menu = ctk.CTkOptionMenu(
            toolbar,
            variable=self._source_filter_var,
            values=["All Sources", "Nix", "Snap", "Flatpak"],
            width=120,
            height=28,
            command=lambda _: self._apply_filter(),
        )
        self._source_menu.pack(side="left", padx=4, pady=4)

        refresh_btn = ctk.CTkButton(
            toolbar,
            text="Refresh",
            image=get_icon("refresh", size=(14, 14)),
            compound="left",
            width=90,
            height=28,
            command=self.refresh,
        )
        refresh_btn.pack(side="right", padx=4, pady=4)

        restore_btn = ctk.CTkButton(
            toolbar,
            text="Restore Stack",
            image=get_icon("restore", size=(14, 14)),
            compound="left",
            width=120,
            height=28,
            fg_color="#2980b9",
            hover_color="#3498db",
            command=self._on_restore,
        )
        restore_btn.pack(side="right", padx=4, pady=4)

        export_btn = ctk.CTkButton(
            toolbar,
            text="Export Stack",
            image=get_icon("export", size=(14, 14)),
            compound="left",
            width=120,
            height=28,
            fg_color="#8e44ad",
            hover_color="#9b59b6",
            command=self._on_export,
        )
        export_btn.pack(side="right", padx=4, pady=4)

        upgrade_btn = ctk.CTkButton(
            toolbar,
            text="Upgrade All",
            image=get_icon("upgrade", size=(14, 14)),
            compound="left",
            width=110,
            height=28,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            command=self._on_upgrade_all,
        )
        upgrade_btn.pack(side="right", padx=4, pady=4)

        purge_btn = ctk.CTkButton(
            toolbar,
            text="Deep Purge",
            image=get_icon("purge", size=(14, 14)),
            compound="left",
            width=120,
            height=28,
            fg_color="#78281f",
            hover_color="#922b21",
            command=self._on_purge,
        )
        purge_btn.pack(side="right", padx=4, pady=4)

        uninstall_btn = ctk.CTkButton(
            toolbar,
            text="Uninstall",
            image=get_icon("purge", size=(14, 14)),
            compound="left",
            width=100,
            height=28,
            fg_color="#c0392b",
            hover_color="#e74c3c",
            command=self._on_uninstall,
        )
        uninstall_btn.pack(side="right", padx=4, pady=4)

        # ---- treeview (standard ttk, works well inside CTk) ----------------
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Pkg.Treeview",
            background="#16213e",
            foreground="#e0e0e0",
            fieldbackground="#16213e",
            rowheight=28,
            font=("Segoe UI", 11),
        )
        style.configure(
            "Pkg.Treeview.Heading",
            background="#0f3460",
            foreground="#ffffff",
            font=("Segoe UI", 11, "bold"),
        )
        style.map("Pkg.Treeview", background=[("selected", "#1a1a5e")])

        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(
            tree_frame,
            columns=("name", "version", "source"),
            show="headings",
            style="Pkg.Treeview",
            selectmode="extended",
        )
        self._tree.heading("name", text="Package Name")
        self._tree.heading("version", text="Version")
        self._tree.heading("source", text="Manager / Source")
        self._tree.column("name", width=340, anchor="w")
        self._tree.column("version", width=140, anchor="center")
        self._tree.column("source", width=130, anchor="center")
        self._tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self._tree.configure(yscrollcommand=vsb.set)

        # Context menu
        self._ctx_menu = tk.Menu(self, tearoff=0)
        self._ctx_menu.add_command(label="ℹ️  View Application Details", command=self._on_view_details)
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(label="🗑  Standard Uninstall", command=self._on_uninstall)
        self._ctx_menu.add_command(label="💥  Deep Purge (Complete Clean)", command=self._on_purge)
        self._tree.bind("<Button-3>", self._show_context_menu)
        self._tree.bind("<Double-1>", lambda _: self._on_view_details())

    # ---- public API -------------------------------------------------------

    def refresh(self) -> None:
        """Queue a background reload of all installed packages across Nix, Snap, and Flatpak."""
        self._count_lbl.configure(text="Packages: loading…")
        self._worker.submit(self._fetch_packages)

    # ---- background helpers -----------------------------------------------

    def _fetch_packages(self) -> None:
        try:
            pkgs = asyncio.run(self._pm.list_all_installed())
        except Exception as exc:
            self._log.error("Failed to list installed packages: %s", exc)
            pkgs = []
        self.after(0, self._populate, pkgs)

    def _populate(self, pkgs: List[PackageInfo]) -> None:
        self._cached_packages = pkgs
        self._apply_filter()

    def _apply_filter(self) -> None:
        query = self._search_var.get().strip().lower()
        source_filter = self._source_filter_var.get()

        self._tree.delete(*self._tree.get_children())
        visible_count = 0

        for p in self._cached_packages:
            if source_filter != "All Sources":
                if "Nix" in source_filter and p.source != "Nix":
                    continue
                if "Snap" in source_filter and p.source != "Snap":
                    continue
                if "Flatpak" in source_filter and p.source != "Flatpak":
                    continue

            if query and (query not in p.name.lower() and query not in p.version.lower()):
                continue

            source_badge = p.source
            iid = f"{p.source}::{p.name}"
            self._tree.insert("", "end", iid=iid, values=(p.name, p.version, source_badge))
            visible_count += 1

        total = len(self._cached_packages)
        if visible_count == total:
            self._count_lbl.configure(text=f"Packages: {total}")
        else:
            self._count_lbl.configure(text=f"Showing: {visible_count} / {total}")

    def _on_export(self) -> None:
        if not self._cached_packages:
            show_alert_dialog(self, "Export", "No installed packages found to export.", alert_type="info")
            return

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Software Stack",
            initialfile="nixmanager-stack.json",
            filetypes=[
                ("JSON Stack Manifest (*.json)", "*.json"),
                ("Nix Shell Expression (*.nix)", "*.nix"),
                ("All Files (*.*)", "*.*"),
            ],
        )

        if not file_path:
            return

        try:
            # If exporting .nix, use nix pkgs only; if JSON, export full multi-manager stack
            pkgs_to_export = [p for p in self._cached_packages if p.source.lower() == "nix"] if file_path.endswith(".nix") else self._cached_packages
            saved_path = NixEnvironmentExporter.export_to_file(pkgs_to_export, file_path)
            self._log.info("Exported software stack to: %s", saved_path)
            if self._console_cb:
                self._console_cb("info", f"✓ Software stack ({len(pkgs_to_export)} apps) exported to: {saved_path}")
            show_alert_dialog(
                self,
                "Export Successful",
                f"Software stack successfully exported to:\n{saved_path}\n\nTotal packages saved: {len(pkgs_to_export)}",
                alert_type="info",
            )
        except Exception as exc:
            self._log.error("Failed to export stack: %s", exc)
            show_alert_dialog(self, "Export Failed", f"Could not write file:\n{exc}", alert_type="error")

    def _on_restore(self) -> None:
        """Import and batch-restore a previously exported software stack manifest."""
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Select Software Stack Manifest to Restore",
            filetypes=[
                ("JSON Stack Manifest (*.json)", "*.json"),
                ("All Files (*.*)", "*.*"),
            ],
        )
        if not file_path:
            return

        try:
            packages = NixEnvironmentExporter.import_from_file(file_path)
            if not packages:
                show_alert_dialog(self, "Empty Stack", "No package entries found in the selected manifest.", alert_type="warning")
                return

            item_names = [f"{p.name} [{p.source}]" for p in packages]
            confirmed = show_confirm_dialog(
                parent=self,
                title="Confirm Batch Restoration",
                message=f"Found {len(packages)} packages to restore. Do you want to proceed with batch restoration now?",
                items=item_names,
                confirm_text="Restore All",
                cancel_text="Cancel",
            )
            if not confirmed:
                return

            if self._console_cb:
                self._console_cb("info", f"Starting batch restoration of {len(packages)} packages from {file_path}...")

            async def _do_restore():
                def _prog(msg):
                    if self._console_cb:
                        self._console_cb("info", msg)
                return await NixEnvironmentExporter.restore_stack(packages, self._pm, progress_cb=_prog)

            def _on_done(results):
                msg = f"✓ Batch restoration finished! Processed {len(results)} package(s)."
                if self._console_cb:
                    self._console_cb("info", msg)
                DesktopNotifier.info("Restoration Complete", f"Successfully restored {len(results)} package(s).")
                self.refresh()

            def _on_err(err):
                self._log.error("Restore failed: %s", err)
                if self._console_cb:
                    self._console_cb("stderr", f"✗ Batch restoration error: {err}")

            self._worker.submit_async(_do_restore, on_success=_on_done, on_error=_on_err)

        except Exception as exc:
            self._log.error("Failed to load stack: %s", exc)
            show_alert_dialog(self, "Import Error", f"Failed to read stack manifest:\n{exc}", alert_type="error")

    def _on_upgrade_all(self) -> None:
        confirmed = show_confirm_dialog(
            parent=self,
            title="Upgrade All Packages",
            message="This will execute 'nix-env -u' to upgrade all Nix packages in your profile to their latest versions.",
            confirm_text="Upgrade All",
            cancel_text="Cancel",
        )
        if not confirmed:
            return

        self._log.info("User requested upgrade of all packages")
        if self._console_cb:
            self._console_cb("info", "Starting 'nix-env -u' upgrade process (check Console tab for progress)...")
        self._worker.submit(self._upgrade_bg)

    def _upgrade_bg(self) -> None:
        try:
            res = asyncio.run(self._pm.upgrade_all())
            msg = f"✓ Upgrade finished: {res}"
        except Exception as exc:
            msg = f"✗ Upgrade failed: {exc}"
            self._log.error(msg)

        if self._console_cb:
            self._console_cb("info", msg)
        self.after(500, self.refresh)

    def _on_view_details(self) -> None:
        """Open rich details modal card for the selected package."""
        selection = self._tree.selection()
        if not selection:
            return

        iid = selection[0]
        selected_pkg = None
        for p in self._cached_packages:
            if f"{p.source}::{p.name}" == iid or p.name == iid:
                selected_pkg = p
                break

        if not selected_pkg:
            return

        item = resolve_rich_details(selected_pkg.name, source=selected_pkg.source, version=selected_pkg.version)
        if hasattr(self, "_details_dialog") and self._details_dialog and self._details_dialog.winfo_exists():
            try:
                self._details_dialog.destroy()
            except Exception:
                pass
        self._details_dialog = AppDetailsDialog(self, item=item, source=selected_pkg.source)

    # ---- uninstall & purge ------------------------------------------------

    def _show_context_menu(self, event: tk.Event) -> None:
        row = self._tree.identify_row(event.y)
        if row:
            self._tree.selection_set(row)
            self._ctx_menu.tk_popup(event.x_root, event.y_root)

    def _on_uninstall(self) -> None:
        """Standard uninstall."""
        selection = self._tree.selection()
        if not selection:
            show_alert_dialog(self, "Uninstall", "Please select one or more packages from the list first.", alert_type="warning")
            return

        selected_pkgs: list[PackageInfo] = []
        for iid in selection:
            for p in self._cached_packages:
                if f"{p.source}::{p.name}" == iid or p.name == iid:
                    selected_pkgs.append(p)
                    break

        if not selected_pkgs:
            return

        item_tags = [f"{p.name} [{p.source}]" for p in selected_pkgs]
        confirmed = show_confirm_dialog(
            parent=self,
            title="Confirm Package Uninstall",
            message="Uninstall selected package binaries from your environment? Application settings and caches will be kept.",
            items=item_tags,
            danger=False,
            confirm_text="Uninstall",
            cancel_text="Cancel",
        )
        if not confirmed:
            return

        for pkg in selected_pkgs:
            self._log.info("Uninstalling %s package: %s", pkg.source, pkg.name)
            self._worker.submit(self._uninstall_one, pkg)

    def _uninstall_one(self, pkg: PackageInfo) -> None:
        try:
            asyncio.run(self._pm.uninstall_generic(pkg))
            msg = f"✓ Successfully uninstalled {pkg.name} ({pkg.source})"
        except Exception as exc:
            msg = f"✗ Failed to uninstall {pkg.name}: {exc}"
            self._log.error(msg)

        if self._console_cb:
            self._console_cb("info", msg)
        self.after(500, self.refresh)

    def _on_purge(self) -> None:
        """Deep Purge - Eradicates package, configs, cache, and store links."""
        selection = self._tree.selection()
        if not selection:
            show_alert_dialog(self, "Deep Purge", "Please select one or more packages from the list first.", alert_type="warning")
            return

        selected_pkgs: list[PackageInfo] = []
        for iid in selection:
            for p in self._cached_packages:
                if f"{p.source}::{p.name}" == iid or p.name == iid:
                    selected_pkgs.append(p)
                    break

        if not selected_pkgs:
            return

        item_tags = [f"{p.name} [{p.source}]" for p in selected_pkgs]
        consequences = [
            "Remove package binaries and executables from environment",
            "Delete user configuration and cache directories (~/.config, ~/.cache)",
            "Remove desktop application shortcuts and launcher entries",
            "Trigger deep store garbage collection to free disk space",
        ]
        confirmed = show_confirm_dialog(
            parent=self,
            title="Confirm Deep Purge",
            message="This will completely eradicate the selected package(s) from your system as if never installed:",
            details=consequences,
            items=item_tags,
            danger=True,
            confirm_text="Eradicate & Purge",
            cancel_text="Cancel",
        )
        if not confirmed:
            return

        for pkg in selected_pkgs:
            self._log.info("Deep purging %s package: %s", pkg.source, pkg.name)
            if self._console_cb:
                self._console_cb("info", f"💥 Initiating Deep Purge for {pkg.name} ({pkg.source})...")
            self._worker.submit(self._purge_one, pkg)

    def _purge_one(self, pkg: PackageInfo) -> None:
        try:
            summary = asyncio.run(self._pm.purge_generic(pkg))
            msg = f"✓ Deep Purge completed for {pkg.name} ({pkg.source})\n{summary}"
        except Exception as exc:
            msg = f"✗ Deep Purge failed for {pkg.name}: {exc}"
            self._log.error(msg)

        if self._console_cb:
            for line in msg.splitlines():
                self._console_cb("info", line)
        self.after(500, self.refresh)
