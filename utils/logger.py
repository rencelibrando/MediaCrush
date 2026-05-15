"""In-memory + file logger."""
from __future__ import annotations
import logging
import os
from pathlib import Path
from datetime import datetime
from collections import deque

LOG_DIR  = Path.home() / ".config" / "mediacrush" / "logs"
MAX_MEM  = 5000  # lines kept in memory


class AppLogger:
    def __init__(self):
        self._lines: deque[str] = deque(maxlen=MAX_MEM)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._file = LOG_DIR / f"session_{stamp}.log"
        self._fh   = open(self._file, "w", buffering=1, encoding="utf-8")

    def append(self, msg: str):
        self._lines.append(msg)
        try:
            self._fh.write(msg + "\n")
        except Exception:
            pass

    def get_all(self) -> list[str]:
        return list(self._lines)

    def export(self, path: Path):
        path.write_text("\n".join(self._lines), encoding="utf-8")

    def close(self):
        try:
            self._fh.close()
        except Exception:
            pass

    @property
    def log_file(self) -> Path:
        return self._file


# Singleton
_logger: AppLogger | None = None


def get_logger() -> AppLogger:
    global _logger
    if _logger is None:
        _logger = AppLogger()
    return _logger
