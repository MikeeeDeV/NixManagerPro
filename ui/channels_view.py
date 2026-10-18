"""
ui.channels_view
~~~~~~~~~~~~~~~~

Smart Nix Channel Manager:
- Curated presets gallery (nixpkgs-unstable, nixos-24.05 stable, home-manager, rust-overlay).
- 1-click subscription and channel switching.
- Targeted single-channel update & full channel update with real-time download terminal.
- Channel health check and ping latency indicator.
- Channel rollback support.
"""

from __future__ import annotations

import asyncio
import logging
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Dict, List, Optional

import customtkinter as ctk

from core.channels import CURATED_CHANNEL_PRESETS, ChannelInfo, ChannelPreset, NixChannelManager
from utils.icons import get_icon
from utils.notifications import DesktopNotifier
from .modern_dialog import show_alert_dialog, show_confirm_dialog

if TYPE_CHECKING:
    from utils.worker import WorkerPool


class ChannelsView(ctk.CTkFrame):
    """Smart Nix Channels Hub with presets, health probe, and real-time streaming."""

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
        self._active_channels: List[ChannelInfo] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ─── 1. Top Section: Smart Preset & Subscribe Bar ────────────────────
        preset_frame = ctk.CTkFrame(self, corner_radius=10)
        preset_frame.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 6))
        preset_frame.grid_columnconfigure(1, weight=1)

        # Row 1: Presets Dropdown & Quick Actions
        ctk.CTkLabel(
            preset_frame,
            text="Smart Presets:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, padx=(12, 6), pady=(10, 4), sticky="w")

        preset_labels = ["-- Select a Curated Channel Preset --"] + [
            f"{p.name} [{p.tag}] — {p.description[:45]}..."
            for p in CURATED_CHANNEL_PRESETS
        ]
        self._preset_var = tk.StringVar(value=preset_labels[0])
        self._preset_menu = ctk.CTkOptionMenu(
            preset_frame,
            values=preset_labels,
            variable=self._preset_var,
            width=420,
            command=self._on_preset_selected,
        )
        self._preset_menu.grid(row=0, column=1, padx=6, pady=(10, 4), sticky="ew")

        # Row 2: Manual / Populated Fields
        inputs_box = ctk.CTkFrame(preset_frame, fg_color="transparent")
        inputs_box.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(4, 10))
        inputs_box.grid_columnconfigure(1, weight=1)

        self._name_var = tk.StringVar(value="nixpkgs")
        self._name_entry = ctk.CTkEntry(
            inputs_box,
            textvariable=self._name_var,
            placeholder_text="Channel Name (e.g. nixpkgs)",
            width=160,
        )
        self._name_entry.pack(side="left", padx=(2, 6))

        self._url_var = tk.StringVar(value="https://nixos.org/channels/nixpkgs-unstable")
        self._url_entry = ctk.CTkEntry(
            inputs_box,
            textvariable=self._url_var,
            placeholder_text="Channel Upstream URL",
        )
        self._url_entry.pack(side="left", padx=6, fill="x", expand=True)

        self._add_btn = ctk.CTkButton(
            inputs_box,
            text="Subscribe / Switch",
            image=get_icon("plus", size=(14, 14)),
            compound="left",
            width=160,
            fg_color="#2980b9",
            hover_color="#3498db",
            command=self._on_add,
        )
        self._add_btn.pack(side="right", padx=(6, 2))

        # ─── 2. Action Toolbar ──────────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, height=44, corner_radius=10)
        toolbar.grid(row=1, column=0, sticky="ew", padx=14, pady=4)

        self._status_lbl = ctk.CTkLabel(
            toolbar, text="Channels: –", font=ctk.CTkFont(weight="bold")
        )
        self._status_lbl.pack(side="left", padx=12)

        refresh_btn = ctk.CTkButton(
            toolbar,
            text="Refresh",
            image=get_icon("refresh", size=(14, 14)),
            compound="left",
            width=90,
            command=self.refresh,
        )
        refresh_btn.pack(side="right", padx=4, pady=6)

        rollback_btn = ctk.CTkButton(
            toolbar,
            text="Rollback",
            image=get_icon("history", size=(14, 14)),
            compound="left",
            width=110,
            fg_color="#d35400",
            hover_color="#e67e22",
            command=self._on_rollback,
        )
        rollback_btn.pack(side="right", padx=4, pady=6)

        remove_btn = ctk.CTkButton(
            toolbar,
            text="Remove Channel",
            image=get_icon("purge", size=(14, 14)),
            compound="left",
            width=130,
            fg_color="#c0392b",
            hover_color="#e74c3c",
            command=self._on_remove,
        )
        remove_btn.pack(side="right", padx=4, pady=6)

        self._btn_update_single = ctk.CTkButton(
            toolbar,
            text="Update Selected",
            image=get_icon("refresh", size=(14, 14)),
            compound="left",
            width=140,
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self._on_update_selected,
        )
        self._btn_update_single.pack(side="right", padx=4, pady=6)

        self._btn_update_all = ctk.CTkButton(
            toolbar,
            text="Update All Channels",
            image=get_icon("refresh", size=(14, 14)),
            compound="left",
            width=160,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            command=self._on_update_all,
        )
        self._btn_update_all.pack(side="right", padx=4, pady=6)

        # ─── 3. Channels Table ──────────────────────────────────────────────
        table_container = ctk.CTkFrame(self, corner_radius=10)
        table_container.grid(row=2, column=0, sticky="nsew", padx=14, pady=4)
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure(
            "Chan.Treeview",
            background="#16213e",
            foreground="#e0e0e0",
            fieldbackground="#16213e",
            rowheight=32,
            font=("Segoe UI", 11),
        )
        style.configure(
            "Chan.Treeview.Heading",
            background="#0f3460",
            foreground="#ffffff",
            font=("Segoe UI", 11, "bold"),
        )
        style.map("Chan.Treeview", background=[("selected", "#1f4068")])

        cols = ("name", "tag", "status", "url")
        self._tree = ttk.Treeview(
            table_container,
            columns=cols,
            show="headings",
            style="Chan.Treeview",
            selectmode="browse",
        )
        self._tree.heading("name", text="Channel Name")
        self._tree.heading("tag", text="Track / Type")
        self._tree.heading("status", text="Health / Ping")
        self._tree.heading("url", text="Upstream Repository URL")

        self._tree.column("name", width=180, anchor="w")
        self._tree.column("tag", width=130, anchor="center")
        self._tree.column("status", width=130, anchor="center")
        self._tree.column("url", width=520, anchor="w")
        self._tree.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=6)

        vsb = ttk.Scrollbar(table_container, orient="vertical", command=self._tree.yview)
        vsb.grid(row=0, column=1, sticky="ns", padx=(0, 6), pady=6)
        self._tree.configure(yscrollcommand=vsb.set)

        # ─── 4. Embedded Live Download Stream Terminal ──────────────────────
        log_frame = ctk.CTkFrame(self, height=130, corner_radius=10)
        log_frame.grid(row=3, column=0, sticky="ew", padx=14, pady=(4, 10))
        log_frame.grid_columnconfigure(0, weight=1)

        header_bar = ctk.CTkFrame(log_frame, fg_color="transparent")
        header_bar.pack(fill="x", padx=10, pady=(6, 2))

        ctk.CTkLabel(
            header_bar,
            text=" Live Channel Download & Unpack Stream:",
            image=get_icon("terminal", size=(14, 14)),
            compound="left",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header_bar,
            text="Clear Output",
            width=80,
            height=20,
            font=ctk.CTkFont(size=10),
            command=self._clear_stream,
        ).pack(side="right")

        self._terminal = ctk.CTkTextbox(
            log_frame,
            height=90,
            font=ctk.CTkFont(family="monospace", size=10),
            fg_color="#0d1117",
            text_color="#c9d1d9",
            wrap="word",
        )
        self._terminal.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        self._terminal.insert("end", "Channels Manager ready. Select a preset or click 'Update' to begin.\n")
        self._terminal.configure(state="disabled")

    # ─── Presets & UI Handlers ──────────────────────────────────────────────

    def _on_preset_selected(self, choice: str) -> None:
        """Populate inputs from selected preset."""
        for preset in CURATED_CHANNEL_PRESETS:
            if choice.startswith(preset.name):
                self._name_var.set(preset.name)
                self._url_var.set(preset.url)
                self._log_stream(f"Selected preset '{preset.name}': {preset.description}")
                break

    def _log_stream(self, text: str) -> None:
        self._terminal.configure(state="normal")
        self._terminal.insert("end", f"{text}\n")
        self._terminal.configure(state="disabled")
        self._terminal.see("end")
        if self._console_cb:
            self._console_cb("stdout", f"[Channels] {text}")

    def _clear_stream(self) -> None:
        self._terminal.configure(state="normal")
        self._terminal.delete("1.0", "end")
        self._terminal.configure(state="disabled")

    # ─── Public API ─────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Fetch registered channels and check their upstream connectivity."""
        self._status_lbl.configure(text="Loading channels…")
        self._worker.submit(self._fetch_channels_bg)

    def _fetch_channels_bg(self) -> None:
        try:
            chans = asyncio.run(self._cm.list_channels())
        except Exception as exc:
            self._log.error("Failed to query channels: %s", exc)
            chans = []
        self.after(0, self._populate, chans)

    def _populate(self, chans: List[ChannelInfo]) -> None:
        self._active_channels = chans
        self._tree.delete(*self._tree.get_children())

        for c in chans:
            # Determine channel tag
            tag = "Custom"
            for preset in CURATED_CHANNEL_PRESETS:
                if preset.url.rstrip("/") in c.url.rstrip("/") or preset.name == c.name:
                    tag = preset.tag
                    break

            self._tree.insert(
                "",
                "end",
                iid=c.name,
                values=(c.name, tag, "Checking...", c.url),
            )

        self._status_lbl.configure(text=f"Active Channels: {len(chans)}")

        # Probe health asynchronously
        for c in chans:
            self._worker.submit(self._probe_channel, c.name, c.url)

    def _probe_channel(self, name: str, url: str) -> None:
        try:
            health = asyncio.run(self._cm.check_channel_health(url))
            latency = health.get("latency_ms", 0)
            status_text = f"Online ({latency}ms)" if health.get("status") == "Online" else "Unreachable"
        except Exception:
            status_text = "Unknown"

        def _update_row():
            if self._tree.exists(name):
                current_values = list(self._tree.item(name, "values"))
                if len(current_values) >= 3:
                    current_values[2] = status_text
                    self._tree.item(name, values=current_values)

        self.after(0, _update_row)

    # ─── Operations ─────────────────────────────────────────────────────────

    def _on_add(self) -> None:
        name = self._name_var.get().strip()
        url = self._url_var.get().strip()
        if not name or not url:
            show_alert_dialog(self, "Missing Info", "Please enter both channel name and URL.", alert_type="warning")
            return

        self._add_btn.configure(state="disabled")
        self._log_stream(f"Subscribing to channel '{name}' from: {url}...")

        async def _add():
            await self._cm.add_channel(name, url)

        def _done(_):
            self._log_stream(f"✓ Channel '{name}' subscribed successfully!")
            DesktopNotifier.info("Channel Subscribed", f"Successfully subscribed to {name}")
            self._add_btn.configure(state="normal")
            self.refresh()

        def _err(e):
            self._log_stream(f"✗ Failed to add channel: {e}")
            self._add_btn.configure(state="normal")

        self._worker.submit_async(_add, on_success=_done, on_error=_err)

    def _on_remove(self) -> None:
        sel = self._tree.selection()
        if not sel:
            show_alert_dialog(self, "Select Channel", "Please select a channel from the table to remove.", alert_type="info")
            return
        name = str(sel[0])

        confirmed = show_confirm_dialog(
            parent=self,
            title="Confirm Channel Removal",
            message=f"Are you sure you want to remove channel '{name}'?",
            danger=True,
            confirm_text="Remove Channel",
            cancel_text="Cancel",
        )
        if not confirmed:
            return

        self._log_stream(f"Removing channel subscription '{name}'...")

        async def _rem():
            await self._cm.remove_channel(name)

        def _done(_):
            self._log_stream(f"✓ Channel '{name}' removed.")
            DesktopNotifier.info("Channel Removed", f"Successfully removed {name}")
            self.refresh()

        def _err(e):
            self._log_stream(f"✗ Failed to remove channel: {e}")

        self._worker.submit_async(_rem, on_success=_done, on_error=_err)

    def _on_update_selected(self) -> None:
        sel = self._tree.selection()
        if not sel:
            show_alert_dialog(self, "Select Channel", "Please select a channel from the table to update.", alert_type="info")
            return
        name = str(sel[0])

        self._btn_update_single.configure(state="disabled")
        self._log_stream(f"Running 'nix-channel --update {name}'...")

        # Hook live command stream to mini-terminal
        orig_cb = self._cm._exec._on_output

        def custom_stream(stream, line):
            if orig_cb:
                orig_cb(stream, line)
            self.after(0, self._log_stream, line)

        self._cm._exec.set_output_callback(custom_stream)

        async def _upd():
            return await self._cm.update_single_channel(name)

        def _done(out):
            self._cm._exec.set_output_callback(orig_cb)
            self._log_stream(f"✓ {out}")
            DesktopNotifier.info("Channel Updated", f"Channel {name} updated to latest revisions.")
            self._btn_update_single.configure(state="normal")
            self.refresh()

        def _err(e):
            self._cm._exec.set_output_callback(orig_cb)
            self._log_stream(f"✗ Channel update error: {e}")
            self._btn_update_single.configure(state="normal")

        self._worker.submit_async(_upd, on_success=_done, on_error=_err)

    def _on_update_all(self) -> None:
        self._btn_update_all.configure(state="disabled")
        self._log_stream("Running 'nix-channel --update' for all registered channels...")

        orig_cb = self._cm._exec._on_output

        def custom_stream(stream, line):
            if orig_cb:
                orig_cb(stream, line)
            self.after(0, self._log_stream, line)

        self._cm._exec.set_output_callback(custom_stream)

        async def _upd_all():
            return await self._cm.update_channels()

        def _done(out):
            self._cm._exec.set_output_callback(orig_cb)
            self._log_stream(f"✓ {out}")
            DesktopNotifier.info("Channels Updated", "All Nix channels pulled latest revisions successfully.")
            self._btn_update_all.configure(state="normal")
            self.refresh()

        def _err(e):
            self._cm._exec.set_output_callback(orig_cb)
            self._log_stream(f"✗ Update error: {e}")
            self._btn_update_all.configure(state="normal")

        self._worker.submit_async(_upd_all, on_success=_done, on_error=_err)

    def _on_rollback(self) -> None:
        confirmed = show_confirm_dialog(
            parent=self,
            title="Confirm Channel Rollback",
            message="Rollback channels to previous generation via 'nix-channel --rollback'?",
            confirm_text="Rollback",
            cancel_text="Cancel",
        )
        if not confirmed:
            return

        self._log_stream("Rolling back channels to previous generation...")

        async def _rb():
            return await self._cm.rollback()

        def _done(out):
            self._log_stream(f"✓ {out}")
            DesktopNotifier.info("Channel Rollback", "Successfully rolled back channels.")
            self.refresh()

        def _err(e):
            self._log_stream(f"✗ Rollback failed: {e}")

        self._worker.submit_async(_rb, on_success=_done, on_error=_err)
