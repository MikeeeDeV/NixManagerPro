"""
utils.worker
~~~~~~~~~~~~~

Thread‑safe worker pool for offloading blocking / CPU‑bound tasks from the
Tk main thread.

The pool accepts ``(callable, args, kwargs)`` tuples via a :class:`queue.Queue`
and executes them on daemon threads.  Exceptions are logged — they never
propagate back to the caller's thread.

For tasks that need to post results back to the UI, the callable itself
should use ``widget.after(0, callback, …)`` to marshal data to the Tk loop.
"""

from __future__ import annotations

import queue
import threading
from typing import Any, Callable, Optional


class WorkerPool:
    """
    A minimal, pre‑heated thread pool.

    Parameters
    ----------
    max_workers:
        Number of daemon threads to spin up.
    """

    def __init__(self, max_workers: int = 4) -> None:
        self._queue: queue.Queue = queue.Queue()
        self._threads = [
            threading.Thread(
                target=self._loop,
                name=f"Worker-{i}",
                daemon=True,
            )
            for i in range(max_workers)
        ]
        for t in self._threads:
            t.start()

    # ---- public API -------------------------------------------------------

    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> None:
        """Enqueue *fn* for background execution."""
        self._queue.put((fn, args, kwargs))

    def pending(self) -> int:
        """Approximate number of tasks waiting to run."""
        return self._queue.qsize()

    # ---- internals --------------------------------------------------------

    def _loop(self) -> None:
        """Main loop executed on each worker thread."""
        while True:
            fn, args, kwargs = self._queue.get()
            try:
                fn(*args, **kwargs)
            except Exception:
                # Import lazily to avoid circular deps at module‑load time.
                from .logger import get_logger
                get_logger().exception("Uncaught exception in worker thread")
            finally:
                self._queue.task_done()
