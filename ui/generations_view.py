"""
ui.generations_view
~~~~~~~~~~~~~~~~~~~

Dedicated UI component for browsing Nix Generations and executing
instant atomic rollbacks or switching between previous states.
"""

from __future__ import annotations

import asyncio
import logging
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, List

import customtkinter as ctk

from utils.icons import get_icon
from .modern_dialog import show_alert_dialog, show_confirm_dialog

if TYPE_CHECKING:
    from core.generations import GenerationInfo, NixGenerationManager
    from utils.worker import WorkerPool


class GenerationsView(ctk.CTkFrame):
    """Visual timeline of profile states with single-click rollback."""

    def __init__(
        self,
        master: tk.Misc,
        gen_manager: NixGenerationManager,
        worker: WorkerPool,
        logger: logging.Logger,
        console_cb=None,
        on_profile_changed=None,
    ) -> None:
        super().__init__(master)
        self._gm = gen_manager
        self._worker = worker
        self._log = logger
        self._console_cb = console_cb
        self._on_changed = on_profile_changed

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ---- action toolbar ------------------------------------------------
        toolbar = ctk.CTkFrame(self, height=44)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self._status_lbl = ctk.CTkLabel(toolbar, text="Generations: –", font=ctk.CTkFont(weight="bold"))
        self._status_lbl.pack(side="left", padx=10)

        refresh_btn = ctk.CTkButton(
            toolbar,
            text="Refresh",
            image=get_icon("refresh", (16, 16)),
            compound="left",
            width=110,
            command=self.refresh,
        )
        refresh_btn.pack(side="right", padx=6, pady=6)

        self._rollback_btn = ctk.CTkButton(
            toolbar,
            text="Instant Rollback",
            image=get_icon("history", (16, 16)),
            compound="left",
            width=150,
            fg_color="#d35400",
            hover_color="#e67e22",
            command=self._on_rollback,
        )
        self._rollback_btn.pack(side="right", padx=6, pady=6)

        self._switch_btn = ctk.CTkButton(
            toolbar,
            text="Switch to Selected",
            image=get_icon("check", (16, 16)),
            compound="left",
            width=160,
            command=self._on_switch,
        )
        self._switch_btn.pack(side="right", padx=6, pady=6)

        purge_btn = ctk.CTkButton(
            toolbar,
            text="Delete Old",
            image=get_icon("purge", (16, 16)),
            compound="left",
            width=120,
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            command=self._on_purge_old,
        )
        purge_btn.pack(side="right", padx=6, pady=6)

        # ---- treeview history table ---------------------------------------
        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure(
            "Gen.Treeview",
            background="#16213e",
            foreground="#e0e0e0",
            fieldbackground="#16213e",
            rowheight=30,
            font=("Segoe UI", 11),
        )
        style.configure(
            "Gen.Treeview.Heading",
            background="#0f3460",
            foreground="#ffffff",
            font=("Segoe UI", 11, "bold"),
        )
        style.map("Gen.Treeview", background=[("selected", "#1f4068")])

        self._tree = ttk.Treeview(
            tree_frame,
            columns=("id", "status", "timestamp"),
            show="headings",
            style="Gen.Treeview",
            selectmode="browse",
        )
        self._tree.heading("id", text="Gen #")
        self._tree.heading("status", text="Status")
        self._tree.heading("timestamp", text="Created At")

        self._tree.column("id", width=80, anchor="center")
        self._tree.column("status", width=140, anchor="center")
        self._tree.column("timestamp", width=260, anchor="w")
        self._tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self._tree.configure(yscrollcommand=vsb.set)

    def refresh(self) -> None:
        """Trigger background retrieval of generations list."""
        self._status_lbl.configure(text="Loading generations…")
        self._worker.submit(self._fetch_history)

    def _fetch_history(self) -> None:
        try:
            gens = asyncio.run(self._gm.list_generations())
        except Exception as exc:
            self._log.error("Failed to query generations: %s", exc)
            gens = []
        self.after(0, self._populate, gens)

    def _populate(self, gens: List[GenerationInfo]) -> None:
        self._tree.delete(*self._tree.get_children())
        for g in gens:
            status_text = "Active (Current)" if g.is_current else "Historical"
            self._tree.insert(
                "", "end", iid=str(g.id), values=(g.id, status_text, g.timestamp)
            )
        self._status_lbl.configure(text=f"Total Generations: {len(gens)}")

    def _on_rollback(self) -> None:
        confirmed = show_confirm_dialog(
            parent=self,
            title="Confirm Rollback",
            message="Are you sure you want to rollback to the previous profile generation?",
            confirm_text="Rollback",
            cancel_text="Cancel",
        )
        if not confirmed:
            return

        self._log.info("User requested generation rollback")
        if self._console_cb:
            self._console_cb("info", "Executing nix-env --rollback ...")
        self._rollback_btn.configure(state="disabled")
        self._worker.submit(self._rollback_bg)

    def _rollback_bg(self) -> None:
        try:
            res = asyncio.run(self._gm.rollback())
            msg = f"✓ Rollback complete: {res}"
        except Exception as exc:
            msg = f"✗ Rollback failed: {exc}"
            self._log.error(msg)

        if self._console_cb:
            self._console_cb("info", msg)

        self.after(0, self._action_complete)

    def _on_switch(self) -> None:
        sel = self._tree.selection()
        if not sel:
            show_alert_dialog(self, "Select Generation", "Please select a generation from the table.", alert_type="info")
            return

        gen_id = int(sel[0])
        confirmed = show_confirm_dialog(
            parent=self,
            title="Confirm Switch",
            message=f"Switch active profile to Generation #{gen_id}?",
            confirm_text="Switch Generation",
            cancel_text="Cancel",
        )
        if not confirmed:
            return

        self._log.info("Switching to generation %d", gen_id)
        if self._console_cb:
            self._console_cb("info", f"Switching to generation {gen_id}...")
        self._worker.submit(self._switch_bg, gen_id)

    def _switch_bg(self, gen_id: int) -> None:
        try:
            res = asyncio.run(self._gm.switch_generation(gen_id))
            msg = f"✓ {res}"
        except Exception as exc:
            msg = f"✗ Failed switching generation: {exc}"
            self._log.error(msg)

        if self._console_cb:
            self._console_cb("info", msg)

        self.after(0, self._action_complete)

    def _on_purge_old(self) -> None:
        confirmed = show_confirm_dialog(
            parent=self,
            title="Purge Historic Generations",
            message="This will delete all historical generations except the currently active one.",
            danger=True,
            confirm_text="Purge Old",
            cancel_text="Cancel",
        )
        if not confirmed:
            return

        self._log.info("Purging old generations")
        self._worker.submit(self._purge_bg)

    def _purge_bg(self) -> None:
        try:
            res = asyncio.run(self._gm.delete_old())
            msg = f"✓ {res}"
        except Exception as exc:
            msg = f"✗ Purge failed: {exc}"
            self._log.error(msg)

        if self._console_cb:
            self._console_cb("info", msg)

        self.after(0, self._action_complete)

    def _action_complete(self) -> None:
        self._rollback_btn.configure(state="normal")
        self.refresh()
        if self._on_changed:
            self._on_changed()
