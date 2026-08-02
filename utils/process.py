"""Subprocess helpers used by the desktop app."""
from __future__ import annotations

import os
import subprocess


def hidden_subprocess_kwargs() -> dict:
    """Return kwargs that prevent child console windows on Windows."""
    if os.name != "nt":
        return {}
    return {"creationflags": subprocess.CREATE_NO_WINDOW}
