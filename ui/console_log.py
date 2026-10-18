"""
ui.console_log
~~~~~~~~~~~~~~

Live terminal‑style log console that displays real‑time stdout/stderr
from any Nix CLI process.

The widget registers itself as the ``on_output`` callback of the shared
:class:`~core.command_executor.AsyncCommandExecutor`.  Because that callback
fires from a worker thread, every mutation is marshalled to the Tk main loop
via ``widget.after()``.
"""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    from core.command_executor import AsyncCommandExecutor


class ConsoleLog(ctk.CTkFrame):
    """Scrolling, read‑only text area that mimics a terminal."""

    # Colour tags for stream differentiation
    _TAG_STDOUT = "stdout"
    _TAG_STDERR = "stderr"
    _TAG_INFO   = "info"

    def __init__(self, master: tk.Misc, executor: AsyncCommandExecutor) -> None:
        super().__init__(master)
        self._executor = executor

        # ---- widgets ------------------------------------------------------
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._text = tk.Text(
            self,
            state="disabled",
            wrap="word",
            font=("Consolas", 11),
            bg="#1a1a2e",
            fg="#e0e0e0",
            insertbackground="#e0e0e0",
            selectbackground="#3a3a5e",
            relief="flat",
            padx=8,
            pady=8,
        )
        self._text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ctk.CTkScrollbar(self, command=self._text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._text.configure(yscrollcommand=scrollbar.set)

        # Stream colour tags
        self._text.tag_configure(self._TAG_STDOUT, foreground="#a3d9a5")
        self._text.tag_configure(self._TAG_STDERR, foreground="#f28b82")
        self._text.tag_configure(self._TAG_INFO,   foreground="#8ab4f8")

        # ---- toolbar -------------------------------------------------------
        toolbar = ctk.CTkFrame(self, height=36)
        toolbar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        self._clear_btn = ctk.CTkButton(
            toolbar, text="Clear", width=80, command=self.clear,
        )
        self._clear_btn.pack(side="right", padx=6, pady=4)

    # ---- public API -------------------------------------------------------

    def append_line(self, stream: str, line: str) -> None:
        """
        Thread‑safe append.  Called from any thread — marshals to Tk.

        Parameters
        ----------
        stream:
            ``"stdout"`` | ``"stderr"`` | ``"info"``
        line:
            Text to display (trailing newline is added automatically).
        """
        # ``after()`` schedules execution on the Tk main‑loop thread.
        self.after(0, self._insert, stream, line)

    def clear(self) -> None:
        """Erase all console content."""
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")

    # ---- internals --------------------------------------------------------

    def _insert(self, stream: str, line: str) -> None:
        """Actually insert text — must be called on the Tk thread."""
        self._text.configure(state="normal")

        timestamp = datetime.now().strftime("%H:%M:%S")
        tag = stream if stream in (self._TAG_STDOUT, self._TAG_STDERR, self._TAG_INFO) else self._TAG_STDOUT
        prefix = {"stdout": "OUT", "stderr": "ERR", "info": "INF"}.get(stream, "OUT")

        self._text.insert("end", f"[{timestamp}] [{prefix}] {line}\n", tag)
        self._text.configure(state="disabled")
        self._text.see("end")          # auto‑scroll to bottom
