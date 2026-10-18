"""
ui.channels_view
~~~~~~~~~~~~~~~~

UI module for managing Nix package repositories (channels).
Enables listing, registering new upstream URLs, pulling updates, and rolling back.
"""

from __future__ import annotations

import asyncio
import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, List

import customtkinter as ctk

if TYPE_CHECKING:
    from core.channels import ChannelInfo, NixChannelManager
    from utils.worker import WorkerPool


class ChannelsView(ctk.CTkFrame):
    """Channel manager tab with interactive table and actions."""

    def __init__(
        self,
        master: tk.Misc,
        channel_manager: NixChannelManager,
        worker: WorkerPool,
        logger: logging.Logger,
        console_cb=None,
    ) -> None:
        super().__init__(master)
        self._cm = channel_manager
        self._worker = worker
        self._log = logger
        self._console_cb = console_cb

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ---- add channel bar -----------------------------------------------
        add_frame = ctk.CTkFrame(self)
        add_frame.grid(row=0, column=0, sticky="ew", padx=6, pady=(0, 6))

        self._name_var = tk.StringVar(value="nixpkgs")
        self._name_entry = ctk.CTkEntry(
            add_frame, textvariable=self._name_var, placeholder_text="Channel Name (e.g. nixpkgs)", width=180
        )
        self._name_entry.pack(side="left", padx=8, pady=8)

        self._url_var = tk.StringVar()
        self._url_entry = ctk.CTkEntry(
            add_frame,
            textvariable=self._url_var,
            placeholder_text="Channel URL (e.g. https://nixos.org/channels/nixos-unstable)",
            width=420,
        )
        self._url_entry.pack(side="left", padx=6, pady=8, fill="x", expand=True)

        add_btn = ctk.CTkButton(
            add_frame, text="➕  Add / Subscribe", width=150, fg_color="#2980b9", hover_color="#3498db", command=self._on_add
        )
        add_btn.pack(side="right", padx=8, pady=8)

        # ---- action toolbar ------------------------------------------------
        toolbar = ctk.CTkFrame(self, height=44)
        toolbar.grid(row=1, column=0, sticky="ew", padx=6, pady=2)

        self._status_lbl = ctk.CTkLabel(toolbar, text="Channels: –", font=ctk.CTkFont(weight="bold"))
        self._status_lbl.pack(side="left", padx=10)

        refresh_btn = ctk.CTkButton(toolbar, text="⟳  Refresh", width=100, command=self.refresh)
        refresh_btn.pack(side="right", padx=6, pady=6)

        self._update_btn = ctk.CTkButton(
            toolbar,
            text="⬇ Update All Channels",
            width=180,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            command=self._on_update,
        )
        self._update_btn.pack(side="right", padx=6, pady=6)

        remove_btn = ctk.CTkButton(
            toolbar,
            text="🗑 Remove Selected",
            width=150,
            fg_color="#c0392b",
            hover_color="#e74c3c",
            command=self._on_remove,
        )
        remove_btn.pack(side="right", padx=6, pady=6)

        # ---- treeview channels table ---------------------------------------
        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=6, pady=6)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure(
            "Chan.Treeview",
            background="#16213e",
            foreground="#e0e0e0",
            fieldbackground="#16213e",
            rowheight=30,
            font=("Segoe UI", 11),
        )
        style.configure(
            "Chan.Treeview.Heading",
            background="#0f3460",
            foreground="#ffffff",
            font=("Segoe UI", 11, "bold"),
        )
        style.map("Chan.Treeview", background=[("selected", "#1f4068")])

        self._tree = ttk.Treeview(
            tree_frame,
            columns=("name", "url"),
            show="headings",
            style="Chan.Treeview",
            selectmode="browse",
        )
        self._tree.heading("name", text="Channel Name")
        self._tree.heading("url", text="Upstream URL")
        self._tree.column("name", width=180, anchor="w")
        self._tree.column("url", width=600, anchor="w")
        self._tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self._tree.configure(yscrollcommand=vsb.set)

    def refresh(self) -> None:
        """Fetch registered channels in background."""
        self._status_lbl.configure(text="Loading channels…")
        self._worker.submit(self._fetch_channels)

    def _fetch_channels(self) -> None:
        try:
            chans = asyncio.run(self._cm.list_channels())
        except Exception as exc:
            self._log.error("Failed to query channels: %s", exc)
            chans = []
        self.after(0, self._populate, chans)

    def _populate(self, chans: List[ChannelInfo]) -> None:
        self._tree.delete(*self._tree.get_children())
        for c in chans:
            self._tree.insert("", "end", iid=c.name, values=(c.name, c.url))
        self._status_lbl.configure(text=f"Subscribed Channels: {len(chans)}")

    def _on_add(self) -> None:
        name = self._name_var.get().strip()
        url = self._url_var.get().strip()
        if not name or not url:
            messagebox.showwarning("Missing Information", "Please enter both channel name and URL.")
            return

        self._log.info("Adding channel: %s -> %s", name, url)
        if self._console_cb:
            self._console_cb("info", f"Subscribing to channel {name} ({url})...")
        self._worker.submit(self._add_bg, name, url)

    def _add_bg(self, name: str, url: str) -> None:
        try:
            asyncio.run(self._cm.add_channel(name, url))
            msg = f"✓ Subscribed to {name}"
        except Exception as exc:
            msg = f"✗ Failed to add channel: {exc}"
            self._log.error(msg)

        if self._console_cb:
            self._console_cb("info", msg)
        self.after(0, self.refresh)

    def _on_remove(self) -> None:
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Select Channel", "Please select a channel to remove.")
            return
        name = str(sel[0])

        if not messagebox.askyesno("Confirm Remove", f"Remove channel subscription '{name}'?"):
            return

        self._log.info("Removing channel: %s", name)
        self._worker.submit(self._remove_bg, name)

    def _remove_bg(self, name: str) -> None:
        try:
            asyncio.run(self._cm.remove_channel(name))
            msg = f"✓ Channel {name} removed."
        except Exception as exc:
            msg = f"✗ Failed removing channel: {exc}"
            self._log.error(msg)

        if self._console_cb:
            self._console_cb("info", msg)
        self.after(0, self.refresh)

    def _on_update(self) -> None:
        self._log.info("Updating all channels")
        if self._console_cb:
            self._console_cb("info", "Executing nix-channel --update (this may take a few moments)...")
        self._update_btn.configure(state="disabled")
        self._worker.submit(self._update_bg)

    def _update_bg(self) -> None:
        try:
            res = asyncio.run(self._cm.update_channels())
            msg = f"✓ {res}"
        except Exception as exc:
            msg = f"✗ Channel update failed: {exc}"
            self._log.error(msg)

        if self._console_cb:
            self._console_cb("info", msg)
        self.after(0, self._update_done)

    def _update_done(self) -> None:
        self._update_btn.configure(state="normal")
        self.refresh()
