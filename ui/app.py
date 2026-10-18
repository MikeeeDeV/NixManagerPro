"""
ui.app
~~~~~~

WingetUI / UniGetUI-grade desktop application container for NixManager Pro.
Features a modern left navigation sidebar, persistent status monitor,
seamless view switching, and dynamic theme support.
"""

from __future__ import annotations

import webbrowser
import tkinter as tk
from typing import Dict, Optional

import customtkinter as ctk

from core.channels import NixChannelManager
from core.command_executor import AsyncCommandExecutor
from core.diagnostics import Diagnostics
from core.generations import NixGenerationManager
from core.package_manager import NixPackageManager
from utils.config import AppConfig, load_config
from utils.logger import get_logger
from utils.worker import WorkerPool

from .channels_view import ChannelsView
from .console_log import ConsoleLog
from .dashboard import Dashboard
from .generations_view import GenerationsView
from .install_dialog import InstallDialog
from .package_table import PackageTable
from .updates_view import UpdatesView



class NixManagerApp(ctk.CTk):
    """
    Modern WingetUI-style desktop application for Nix package management.
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        super().__init__()

        self.cfg = config or load_config()
        self.logger = get_logger(self.cfg.log_level)

        # ---- window configuration -----------------------------------------
        ctk.set_appearance_mode(self.cfg.theme_mode)
        ctk.set_default_color_theme(self.cfg.colour_theme)
        self.title("NixManager Pro — Nix Desktop Software Center")
        self.geometry(f"{max(self.cfg.window_width, 1180)}x{max(self.cfg.window_height, 760)}")
        self.minsize(980, 640)

        # ---- core services ------------------------------------------------
        self.executor = AsyncCommandExecutor()
        self.pkg_manager = NixPackageManager(self.executor)
        self.diagnostics = Diagnostics(self.executor)
        self.gen_manager = NixGenerationManager(self.executor)
        self.channel_manager = NixChannelManager(self.executor)
        self.worker = WorkerPool(max_workers=self.cfg.max_worker_threads)

        # ---- root layout: sidebar (col 0) | content (col 1) ---------------
        self.grid_columnconfigure(0, weight=0)          # Fixed sidebar
        self.grid_columnconfigure(1, weight=1)          # Expanding content view
        self.grid_rowconfigure(0, weight=1)             # Main workspace
        self.grid_rowconfigure(1, weight=0)             # Bottom status bar

        # ===================================================================
        # 1. LEFT SIDEBAR (WingetUI Style)
        # ===================================================================
        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_rowconfigure(8, weight=1)     # Push bottom controls down

        # App Brand Header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=14, pady=(18, 16), sticky="w")

        brand_lbl = ctk.CTkLabel(
            brand_frame,
            text="❄️ NixManager",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        brand_lbl.pack(side="left")

        ver_badge = ctk.CTkLabel(
            brand_frame,
            text="PRO v1.6.0",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#3498db",
            text_color="#ffffff",
            corner_radius=6,
            padx=5,
            pady=2,
        )
        ver_badge.pack(side="left", padx=(8, 0))

        # Navigation Buttons
        self._nav_buttons: Dict[str, ctk.CTkButton] = {}

        nav_items = [
            ("discover", "🔍  Discover Software"),
            ("installed", "📦  Installed Packages"),
            ("updates", "🔄  Updates & Health"),
            ("generations", "⏱️  Generations & Rollback"),
            ("channels", "📡  Nix Channels"),
            ("console", "🖥️  Live Console Stream"),
        ]

        for idx, (key, label) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                height=38,
                corner_radius=8,
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray75", "gray25"),
                command=lambda k=key: self.show_view(k),
            )
            btn.grid(row=idx, column=0, padx=10, pady=3, sticky="ew")
            self._nav_buttons[key] = btn

        # Bottom Sidebar Tools (Appearance & GC)
        bottom_tools = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_tools.grid(row=9, column=0, padx=12, pady=16, sticky="ew")

        ctk.CTkLabel(bottom_tools, text="Appearance:", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", pady=(0, 2))
        theme_menu = ctk.CTkOptionMenu(
            bottom_tools,
            values=["Dark", "Light", "System"],
            height=28,
            command=self._on_change_theme,
        )
        theme_menu.set(self.cfg.theme_mode)
        theme_menu.pack(fill="x", pady=(0, 8))

        repo_link = ctk.CTkButton(
            bottom_tools,
            text="GitHub Repository ↗",
            height=26,
            fg_color="transparent",
            text_color="#3498db",
            hover_color=("gray85", "gray20"),
            command=lambda: webbrowser.open("https://github.com/MikeeeDeV/NixManagerPro"),
        )
        repo_link.pack(fill="x")

        # ===================================================================
        # 2. MAIN CONTENT CONTAINER & VIEWS
        # ===================================================================
        self.content_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        self._views: Dict[str, ctk.CTkFrame] = {}

        # 1. Console Stream view
        self.console_view = ConsoleLog(master=self.content_container, executor=self.executor)
        self._views["console"] = self.console_view
        self.executor.set_output_callback(self._on_output_stream)

        # 2. Discover view (App Store with Catalog)
        self.discover_view = InstallDialog(
            master=self.content_container,
            pkg_manager=self.pkg_manager,
            worker=self.worker,
            logger=self.logger,
            console_cb=self.console_view.append_line,
        )
        self._views["discover"] = self.discover_view

        # 3. Dedicated Updates Center (WingetUI-style)
        self.updates_view = UpdatesView(
            master=self.content_container,
            pkg_manager=self.pkg_manager,
            worker=self.worker,
            logger=self.logger,
            console_cb=self.console_view.append_line,
        )
        self._views["updates"] = self.updates_view

        # 4. Installed Packages Table (Stand-alone full-page view)
        self.installed_view = PackageTable(
            master=self.content_container,
            pkg_manager=self.pkg_manager,
            worker=self.worker,
            logger=self.logger,
            console_cb=self.console_view.append_line,
        )
        self._views["installed"] = self.installed_view

        # 5. Generations & Rollback
        self.generations_view = GenerationsView(
            master=self.content_container,
            gen_manager=self.gen_manager,
            worker=self.worker,
            logger=self.logger,
            console_cb=self.console_view.append_line,
            on_profile_changed=self.installed_view.refresh,
        )
        self._views["generations"] = self.generations_view


        # 6. Channels view
        self.channels_view = ChannelsView(
            master=self.content_container,
            channel_manager=self.channel_manager,
            worker=self.worker,
            logger=self.logger,
            console_cb=self.console_view.append_line,
        )
        self._views["channels"] = self.channels_view

        # ===================================================================
        # 3. PERSISTENT WINGETUI STATUS BAR (Bottom)
        # ===================================================================
        self.status_bar = ctk.CTkFrame(self, height=32, corner_radius=0)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.status_text = ctk.CTkLabel(
            self.status_bar,
            text="🟢  System Ready  |  Nix Daemon Active  |  Zero UI Freezing",
            font=ctk.CTkFont(size=11),
            text_color="#8ab4f8",
        )
        self.status_text.pack(side="left", padx=12, pady=4)

        view_logs_btn = ctk.CTkButton(
            self.status_bar,
            text="Terminal Logs ↗",
            width=110,
            height=22,
            font=ctk.CTkFont(size=11),
            command=lambda: self.show_view("console"),
        )
        view_logs_btn.pack(side="right", padx=10, pady=4)

        # Set default active view: Discover Software (App Store)
        self._current_view_key = ""
        self.show_view("discover")

        # Lifecycle protocols
        self.protocol("WM_DELETE_WINDOW", self._on_quit)
        self.after(200, self._startup_refresh)
        self.logger.info("NixManager Pro WingetUI container initialised")

    # ---- view switching ----------------------------------------------------

    def show_view(self, key: str) -> None:
        """Switch active view in the main container."""
        if key == self._current_view_key:
            return

        # Hide all views
        for v in self._views.values():
            v.grid_forget()

        # Update sidebar button highlighting
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(
                    fg_color=("#3498db", "#2980b9"),
                    text_color="#ffffff",
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=("gray10", "gray90"),
                )

        # Show target view
        target = self._views.get(key)
        if target:
            target.grid(row=0, column=0, sticky="nsew")
            self._current_view_key = key

    # ---- background stream handler ----------------------------------------

    def _on_output_stream(self, stream: str, line: str) -> None:
        """Broadcast output to console and update the persistent status pill."""
        self.console_view.append_line(stream, line)
        if len(line.strip()) > 3:
            short_line = line.strip()[:65]
            self.after(0, lambda: self.status_text.configure(text=f"⚙️  {short_line}…"))

    # ---- lifecycle helpers -------------------------------------------------

    def _startup_refresh(self) -> None:
        self.updates_view.refresh_all()
        self.installed_view.refresh()
        self.generations_view.refresh()
        self.channels_view.refresh()


    def _on_change_theme(self, mode: str) -> None:
        self.logger.info("Switching appearance mode to: %s", mode)
        ctk.set_appearance_mode(mode)

    def _on_quit(self) -> None:
        self.logger.info("Shutting down NixManager Pro")
        self.destroy()
