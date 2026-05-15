"""Image compression using Pillow + pillow-heif."""
from __future__ import annotations
from pathlib import Path
from typing import Callable, Optional
import shutil
import tempfile
import threading
import os

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_OK = True
except ImportError:
    HEIF_OK = False

from PIL import Image, ExifTags
from .task import CompressionTask, TaskStatus

ProgressCB = Callable[[float], None]

PRESETS = {
    "lossless": {"quality": 100, "optimize": True},
    "high":     {"quality": 92,  "optimize": True},
    "balanced": {"quality": 85,  "optimize": True},
    "small":    {"quality": 70,  "optimize": True},
    "tiny":     {"quality": 55,  "optimize": True},
}


def _resize(img: Image.Image, max_px: Optional[int]) -> Image.Image:
    if not max_px:
        return img
    w, h = img.size
    if max(w, h) <= max_px:
        return img
    ratio = max_px / max(w, h)
    return img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)


def compress_image(task: CompressionTask, settings: dict,
                   progress_cb: ProgressCB,
                   cancel_event: Optional[threading.Event] = None) -> None:
    _cancel = cancel_event or threading.Event()

    try:
        task.status = TaskStatus.RUNNING
        task.start_time = __import__("time").time()
        progress_cb(5.0)

        if _cancel.is_set():
            task.status = TaskStatus.CANCELLED
            progress_cb(100.0)
            return

        src = task.path
        dst = task.output_path
        dst.parent.mkdir(parents=True, exist_ok=True)

        # Re-read orig_size if it wasn't captured at task creation
        if task.orig_size == 0 and src.exists():
            task.orig_size = src.stat().st_size

        preset_name = settings.get("preset", "balanced")
        # Use image_quality (namespaced) to avoid video quality override
        quality     = settings.get("image_quality",
                      settings.get("quality",
                      PRESETS.get(preset_name, {}).get("quality", 85)))
        strip_meta  = settings.get("strip_metadata", False)
        max_px      = settings.get("resize_max_px")  # None = keep original
        lossless    = (preset_name == "lossless")

        progress_cb(15.0)

        with Image.open(src) as img:
            progress_cb(40.0)
            img = _resize(img, max_px)

            fmt = dst.suffix.lower()
            save_kwargs: dict = {"optimize": True}

            if fmt in (".jpg", ".jpeg"):
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")
                save_kwargs["quality"] = quality
                save_kwargs["progressive"] = True
                if not strip_meta:
                    try:
                        exif = img.info.get("exif")
                        if exif:
                            save_kwargs["exif"] = exif
                    except Exception:
                        pass

            elif fmt == ".png":
                compress_level = 1 if lossless else (6 if quality >= 85 else 9)
                save_kwargs["compress_level"] = compress_level
                if strip_meta:
                    img.info.pop("exif", None)

            elif fmt == ".webp":
                save_kwargs["quality"] = quality
                save_kwargs["lossless"] = lossless
                save_kwargs["method"] = 4

            elif fmt == ".gif":
                save_kwargs.pop("optimize", None)
                save_kwargs.pop("quality", None)

            else:
                # Fallback: convert to JPEG
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")
                save_kwargs["quality"] = quality

            progress_cb(70.0)

            if _cancel.is_set():
                task.status = TaskStatus.CANCELLED
                progress_cb(100.0)
                return

            # Write to temp then atomically move
            with tempfile.NamedTemporaryFile(
                suffix=dst.suffix, dir=dst.parent, delete=False
            ) as tmp:
                tmp_path = Path(tmp.name)

            img.save(tmp_path, **save_kwargs)
            progress_cb(90.0)

        new_size = tmp_path.stat().st_size
        # Replace if: compressed is smaller, OR output goes to a different path,
        # OR orig_size was unknown (0) so we can't compare
        should_replace = (new_size < task.orig_size) or (dst != src) or (task.orig_size == 0)
        if should_replace:
            if dst != src and src.exists() and task.output_dir is None:
                src.unlink()
            shutil.move(str(tmp_path), str(dst))  # cross-fs safe
        else:
            tmp_path.unlink(missing_ok=True)
            new_size = task.orig_size

        task.new_size     = new_size
        task.encoder_used = f"Pillow ({preset_name})"
        task.status       = TaskStatus.DONE
        progress_cb(100.0)

    except Exception as e:
        task.status    = TaskStatus.ERROR
        task.error_msg = str(e)
        progress_cb(100.0)
    finally:
        task.end_time = __import__("time").time()
