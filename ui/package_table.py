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

from core.exporter import NixEnvironmentExporter


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
        toolbar = ctk.CTkFrame(self, height=40)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        self._count_lbl = ctk.CTkLabel(toolbar, text="Packages: –")
        self._count_lbl.pack(side="left", padx=10)

        refresh_btn = ctk.CTkButton(
            toolbar, text="⟳  Refresh", width=110, command=self.refresh,
        )
        refresh_btn.pack(side="right", padx=6, pady=4)

        export_btn = ctk.CTkButton(
            toolbar,
            text="📤  Export shell.nix",
            width=150,
            fg_color="#8e44ad",
            hover_color="#9b59b6",
            command=self._on_export,
        )
        export_btn.pack(side="right", padx=6, pady=4)

        upgrade_btn = ctk.CTkButton(
            toolbar,
            text="🚀  Upgrade All",
            width=130,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            command=self._on_upgrade_all,
        )
        upgrade_btn.pack(side="right", padx=6, pady=4)

        uninstall_btn = ctk.CTkButton(
            toolbar, text="🗑  Uninstall Selected", width=160,
            fg_color="#c0392b", hover_color="#e74c3c",
            command=self._on_uninstall,
        )
        uninstall_btn.pack(side="right", padx=6, pady=4)



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
            columns=("name", "version"),
            show="headings",
            style="Pkg.Treeview",
            selectmode="extended",
        )
        self._tree.heading("name", text="Package Name")
        self._tree.heading("version", text="Version")
        self._tree.column("name", width=400, anchor="w")
        self._tree.column("version", width=160, anchor="center")
        self._tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self._tree.configure(yscrollcommand=vsb.set)

        # Context menu
        self._ctx_menu = tk.Menu(self, tearoff=0)
        self._ctx_menu.add_command(label="Uninstall", command=self._on_uninstall)
        self._tree.bind("<Button-3>", self._show_context_menu)

    # ---- public API -------------------------------------------------------

    def refresh(self) -> None:
        """Queue a background reload of the installed packages list."""
        self._count_lbl.configure(text="Packages: loading…")
        self._worker.submit(self._fetch_packages)

    # ---- background helpers -----------------------------------------------

    def _fetch_packages(self) -> None:
        try:
            pkgs = asyncio.run(self._pm.list_installed())
        except Exception as exc:
            self._log.error("Failed to list installed packages: %s", exc)
            pkgs = []
        self.after(0, self._populate, pkgs)

    def _populate(self, pkgs: List[PackageInfo]) -> None:
        self._cached_packages = pkgs
        self._tree.delete(*self._tree.get_children())
        for p in pkgs:
            self._tree.insert("", "end", iid=p.name, values=(p.name, p.version))
        self._count_lbl.configure(text=f"Packages: {len(pkgs)}")

    def _on_export(self) -> None:
        if not self._cached_packages:
            messagebox.showinfo("Export", "No installed packages found to export.")
            return

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Declarative Nix Environment",
            initialfile="shell.nix",
            filetypes=[
                ("Nix Shell Expression (*.nix)", "*.nix"),
                ("JSON Package Manifest (*.json)", "*.json"),
                ("All Files (*.*)", "*.*"),
            ],
        )

        if not file_path:
            return

        try:
            saved_path = NixEnvironmentExporter.export_to_file(self._cached_packages, file_path)
            self._log.info("Exported environment manifest to: %s", saved_path)
            if self._console_cb:
                self._console_cb("info", f"✓ Environment exported to: {saved_path}")
            messagebox.showinfo(
                "Export Successful",
                f"Declarative environment successfully generated!\n\nLocation:\n{saved_path}\n\nYou can run 'nix-shell' inside that directory to recreate this exact environment.",
            )
        except Exception as exc:
            self._log.error("Failed to export environment: %s", exc)
            messagebox.showerror("Export Failed", f"Could not write file:\n{exc}")

    def _on_upgrade_all(self) -> None:
        if not messagebox.askyesno(
            "Upgrade Packages",
            "This will execute 'nix-env -u' to upgrade all packages in your profile to their latest versions.\nProceed?",
        ):
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

    # ---- uninstall --------------------------------------------------------


    def _show_context_menu(self, event: tk.Event) -> None:
        row = self._tree.identify_row(event.y)
        if row:
            self._tree.selection_set(row)
            self._ctx_menu.tk_popup(event.x_root, event.y_root)

    def _on_uninstall(self) -> None:
        selection = self._tree.selection()
        if not selection:
            return

        names: list[str] = []
        for iid in selection:
            item_data = self._tree.item(iid)
            vals = item_data.get("values", ())
            if vals and len(vals) > 0:
                names.append(str(vals[0]))
            else:
                names.append(str(iid))

        if not names:
            return

        if not messagebox.askyesno(
            "Confirm Uninstall",
            f"Remove the following package(s)?\n\n" + "\n".join(names),
        ):
            return
        for name in names:
            self._log.info("Uninstalling package: %s", name)
            self._worker.submit(self._uninstall_one, name)

    def _uninstall_one(self, name: str) -> None:
        try:
            asyncio.run(self._pm.uninstall(name))
            msg = f"✓ Removed {name}"
        except Exception as exc:
            msg = f"✗ Failed to remove {name}: {exc}"
            self._log.error(msg)

        if self._console_cb:
            self._console_cb("info", msg)
        # Auto‑refresh after uninstall
        self.after(500, self.refresh)
