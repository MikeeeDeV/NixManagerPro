"""
ui.app
~~~~~~~

Root :class:`ctk.CTk` window that wires all UI components together with
the backend services.  This is the single place where dependencies are
constructed and injected into child widgets.
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from core.command_executor import AsyncCommandExecutor
from core.diagnostics import Diagnostics
from core.package_manager import NixPackageManager
from utils.config import AppConfig, load_config
from utils.logger import get_logger
from utils.worker import WorkerPool

from .console_log import ConsoleLog
from .dashboard import Dashboard
from .install_dialog import InstallDialog


class NixManagerApp(ctk.CTk):
    """
    Main application window.

    Responsibilities:
    1. Instantiate all core services (executor, package manager, diagnostics).
    2. Build the tabbed UI (Dashboard | Install | Console).
    3. Wire the executor's output callback → console widget.
    4. Handle graceful shutdown.
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        super().__init__()

        self.cfg = config or load_config()
        self.logger = get_logger(self.cfg.log_level)

        # ---- appearance ---------------------------------------------------
        ctk.set_appearance_mode(self.cfg.theme_mode)
        ctk.set_default_color_theme(self.cfg.colour_theme)
        self.title("NixManager Pro")
        self.geometry(f"{self.cfg.window_width}x{self.cfg.window_height}")
        self.minsize(900, 600)

        # ---- core services ------------------------------------------------
        self.executor = AsyncCommandExecutor()
        self.pkg_manager = NixPackageManager(self.executor)
        self.diagnostics = Diagnostics(self.executor)
        self.worker = WorkerPool(max_workers=self.cfg.max_worker_threads)

        # ---- root grid ----------------------------------------------------
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---- tab view -----------------------------------------------------
        self.tabs = ctk.CTkTabview(self, anchor="nw")
        self.tabs.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Console tab (created first so other widgets can reference its callback)
        console_master = self.tabs.add("🖥  Console")
        self.console = ConsoleLog(master=console_master, executor=self.executor)
        self.console.pack(fill="both", expand=True)

        # Wire executor → console
        self.executor.set_output_callback(self.console.append_line)

        # Dashboard tab
        dash_master = self.tabs.add("📊  Dashboard")
        self.dashboard = Dashboard(
            master=dash_master,
            pkg_manager=self.pkg_manager,
            diagnostics=self.diagnostics,
            worker=self.worker,
            logger=self.logger,
            console_cb=self.console.append_line,
        )
        self.dashboard.pack(fill="both", expand=True)

        # Install tab
        install_master = self.tabs.add("⬇  Install")
        self.installer = InstallDialog(
            master=install_master,
            pkg_manager=self.pkg_manager,
            worker=self.worker,
            logger=self.logger,
            console_cb=self.console.append_line,
        )
        self.installer.pack(fill="both", expand=True)

        # Default visible tab
        self.tabs.set("📊  Dashboard")

        # ---- graceful shutdown -------------------------------------------
        self.protocol("WM_DELETE_WINDOW", self._on_quit)

        # ---- auto‑refresh on startup -------------------------------------
        self.after(200, self.dashboard.refresh_all)
        self.logger.info("NixManager Pro UI initialised")

    # ------------------------------------------------------------------

    def _on_quit(self) -> None:
        self.logger.info("Shutting down NixManager Pro")
        self.destroy()
