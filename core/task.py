from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import uuid
import time

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.avif', '.heic', '.heif',
              '.bmp', '.tiff', '.tif', '.gif'}
VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv',
              '.wmv', '.m4v', '.mpeg', '.mpg'}


class TaskStatus(Enum):
    QUEUED    = "Queued"
    RUNNING   = "Running"
    DONE      = "Done"
    ERROR     = "Error"
    SKIPPED   = "Skipped"
    CANCELLED = "Cancelled"
    PAUSED    = "Paused"


class MediaType(Enum):
    IMAGE   = "image"
    VIDEO   = "video"
    UNKNOWN = "unknown"


@dataclass
class CompressionTask:
    path:       Path
    output_dir: Optional[Path] = None
    id:         str  = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status:     TaskStatus = TaskStatus.QUEUED
    media_type: MediaType  = MediaType.UNKNOWN
    progress:   float = 0.0
    orig_size:  int   = 0
    new_size:   int   = 0
    error_msg:  str   = ""
    start_time: float = 0.0
    end_time:   float = 0.0
    encoder_used: str = ""

    def __post_init__(self):
        ext = self.path.suffix.lower()
        if ext in IMAGE_EXTS:
            self.media_type = MediaType.IMAGE
        elif ext in VIDEO_EXTS:
            self.media_type = MediaType.VIDEO
        if self.path.exists():
            self.orig_size = self.path.stat().st_size

    @property
    def output_path(self) -> Path:
        out_dir = self.output_dir or self.path.parent
        ext = self.path.suffix.lower()
        if self.media_type == MediaType.VIDEO:
            return out_dir / self.path.with_suffix('.mp4').name
        if ext in {'.heic', '.heif', '.bmp', '.tiff', '.tif', '.avif'}:
            return out_dir / self.path.with_suffix('.jpg').name
        return out_dir / self.path.name

    @property
    def saved_bytes(self) -> int:
        return max(0, self.orig_size - self.new_size)

    @property
    def saved_pct(self) -> float:
        if self.orig_size == 0:
            return 0.0
        return max(0.0, (1 - self.new_size / self.orig_size) * 100)

    @property
    def duration(self) -> float:
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return 0.0

    @staticmethod
    def fmt_size(b: int) -> str:
        for u in ('B', 'KB', 'MB', 'GB'):
            if abs(b) < 1024:
                return f"{b:.1f} {u}"
            b /= 1024
        return f"{b:.1f} TB"
