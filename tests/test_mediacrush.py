"""Comprehensive test suite for MediaCrush: theming, WCAG AA, performance, memory safety, and threading."""
import os
import sys
import unittest
import tempfile
import threading
import time
from pathlib import Path
from PIL import Image

# Ensure offscreen Qt platform for headless test execution
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor

# Initialize single QApplication instance for tests
app = QApplication.instance() or QApplication(sys.argv)

from core.task import CompressionTask, TaskStatus, MediaType
from core.engine import CompressionEngine
from core.image_compressor import compress_image
from core.video_compressor import _run_ffmpeg
from gui.styles import get_style, DARK, LIGHT
from gui.widgets.queue_widget import QueueWidget, TaskModel, TaskDelegate
from gui.widgets.logs_widget import LogsWidget, _to_html, _classify
from gui.widgets.drop_zone import DropZone
from gui.widgets.stats_widget import StatsWidget
from gui.widgets.perf_widget import PerfWidget
from gui.main_window import MainWindow
from config.settings import Settings


def _luminance(r: int, g: int, b: int) -> float:
    def _c(val: float) -> float:
        v = val / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * _c(r) + 0.7152 * _c(g) + 0.0722 * _c(b)


def contrast_ratio(hex1: str, hex2: str) -> float:
    c1 = QColor(hex1)
    c2 = QColor(hex2)
    l1 = _luminance(c1.red(), c1.green(), c1.blue())
    l2 = _luminance(c2.red(), c2.green(), c2.blue())
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


class TestThemingAndWCAG(unittest.TestCase):
    def test_dark_mode_contrast(self):
        bg = "#18181b"
        card_bg = "#27272a"

        # Primary text must exceed 4.5:1 (normal text) and 7:1 (AAA)
        ratio_primary = contrast_ratio("#f4f4f5", bg)
        self.assertGreater(ratio_primary, 10.0, f"Primary text contrast too low: {ratio_primary}")

        # Secondary text (#a1a1aa) must exceed WCAG AA 4.5:1
        ratio_secondary = contrast_ratio("#a1a1aa", bg)
        self.assertGreater(ratio_secondary, 5.0, f"Secondary text contrast too low: {ratio_secondary}")

        # Accent button contrast on card
        ratio_accent = contrast_ratio("#ffffff", "#2563eb")
        self.assertGreater(ratio_accent, 4.5)

    def test_light_mode_contrast(self):
        bg = "#f8fafc"
        panel_bg = "#ffffff"

        # Primary text (#0f172a) on white
        ratio_primary = contrast_ratio("#0f172a", panel_bg)
        self.assertGreater(ratio_primary, 12.0)

        # Secondary text (#475569) on white must exceed 4.5:1
        ratio_secondary = contrast_ratio("#475569", panel_bg)
        self.assertGreater(ratio_secondary, 4.5)

        # Log info text (#475569) on white
        ratio_log = contrast_ratio("#475569", "#ffffff")
        self.assertGreater(ratio_log, 4.5)

    def test_queue_delegate_theme_switching(self):
        delegate = TaskDelegate()
        delegate.set_theme("dark")
        self.assertEqual(delegate._name_color.name(), "#f4f4f5")

        delegate.set_theme("light")
        self.assertEqual(delegate._name_color.name(), "#0f172a")

        # In light mode, name color must have high contrast with white background
        ratio = contrast_ratio(delegate._name_color.name(), "#ffffff")
        self.assertGreater(ratio, 10.0)

    def test_logs_widget_theming_and_classification(self):
        widget = LogsWidget()
        widget.set_theme("dark")
        widget.append_line("[OK] image.png compressed")
        widget.append_line("Starting 4 workers")
        widget.append_line("[ERR] file failed")

        self.assertEqual(len(widget._lines), 3)

        # Verify HTML colors in light mode avoid white/invisible text
        html_light = _to_html("Starting 4 workers", theme="light")
        self.assertIn("#0f172a", html_light)

        html_dark = _to_html("Starting 4 workers", theme="dark")
        self.assertIn("#f4f4f5", html_dark)

        # Ensure no emojis in classification
        self.assertEqual(_classify("[OK] done"), "ok")
        self.assertEqual(_classify("[ERR] failed"), "error")


class TestPerformanceAndBatching(unittest.TestCase):
    def test_task_model_batched_insertion(self):
        model = TaskModel()
        dummy_path = Path("/tmp/dummy_file.jpg")
        tasks = [CompressionTask(path=dummy_path) for _ in range(300)]

        t0 = time.perf_counter()
        model.add_tasks(tasks)
        elapsed = time.perf_counter() - t0

        self.assertEqual(model.rowCount(), 300)
        self.assertLess(elapsed, 0.1, f"Batched insertion took too long: {elapsed}s")

    def test_perf_poller_lifecycle(self):
        widget = PerfWidget()
        # Poller thread should be alive
        self.assertTrue(widget._poller._thread.is_alive())

        widget._poller.stop()
        widget._poller._thread.join(timeout=3.0)
        self.assertFalse(widget._poller._thread.is_alive())


class TestMemorySafety(unittest.TestCase):
    def test_image_compressor_cleanup_on_success_and_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            src_img = tmp_path / "test.jpg"
            out_dir = tmp_path / "out"

            # Create dummy JPEG
            im = Image.new("RGB", (100, 100), color=(200, 50, 50))
            im.save(src_img)

            task = CompressionTask(path=src_img, output_dir=out_dir)
            settings = {"preset": "balanced", "quality": 80}

            def _nop(pct): pass

            compress_image(task, settings, _nop)
            self.assertEqual(task.status, TaskStatus.DONE)
            self.assertTrue(task.output_path.exists())

            # Check that no temporary files were leaked in output directory
            temp_files = list(out_dir.glob(".tmp_mc_*"))
            self.assertEqual(len(temp_files), 0, f"Leaked temp files found: {temp_files}")

            # Test cleanup on cancelled task
            cancel_evt = threading.Event()
            cancel_evt.set()
            task_cancel = CompressionTask(path=src_img, output_dir=out_dir)
            compress_image(task_cancel, settings, _nop, cancel_event=cancel_evt)
            self.assertEqual(task_cancel.status, TaskStatus.CANCELLED)

            temp_files_cancel = list(out_dir.glob(".tmp_mc_*"))
            self.assertEqual(len(temp_files_cancel), 0)

    def test_logs_widget_memory_bounds(self):
        widget = LogsWidget()
        widget._max_lines = 100
        for i in range(150):
            widget.append_line(f"Log message {i}")

        self.assertLessEqual(len(widget._lines), 100)
        self.assertLessEqual(len(widget._filtered), 100)


class TestThreadingAndEngine(unittest.TestCase):
    def test_engine_clear_queue_thread_safe(self):
        engine = CompressionEngine()
        tasks = [CompressionTask(path=Path(f"/tmp/file_{i}.jpg")) for i in range(10)]
        engine.add_tasks(tasks)
        self.assertEqual(len(engine.get_tasks()), 10)

        engine.clear_queue()
        self.assertEqual(len(engine.get_tasks()), 0)

    def test_engine_cancel_responsiveness(self):
        engine = CompressionEngine()
        t = CompressionTask(path=Path("/tmp/nonexistent.mp4"))
        engine.add_task(t)

        engine.cancel()
        tasks = engine.get_tasks()
        self.assertEqual(tasks[0].status, TaskStatus.CANCELLED)

    def test_ffmpeg_pipe_cancellation_safety(self):
        # Run a sleeping process with _run_ffmpeg to test cancel event
        cancel_evt = threading.Event()

        def _trigger_cancel():
            time.sleep(0.1)
            cancel_evt.set()

        threading.Thread(target=_trigger_cancel, daemon=True).start()

        cmd = ["sleep", "5"]
        t0 = time.time()
        rc, err = _run_ffmpeg(cmd, duration=5.0, progress_cb=lambda p: None,
                              cancel_event=cancel_evt)
        elapsed = time.time() - t0

        self.assertLess(elapsed, 1.5, f"Cancellation took too long: {elapsed}s")


class TestMainWindowIntegration(unittest.TestCase):
    def test_main_window_instantiation_and_theme_toggle(self):
        win = MainWindow()
        win.show()

        # Test initial dark theme
        win._settings.set("ui.theme", "dark")
        win._apply_theme()
        self.assertEqual(win.queue_widget._delegate._theme, "dark")

        # Test toggle to light theme
        win._toggle_theme()
        self.assertEqual(win._settings.get("ui.theme"), "light")
        self.assertEqual(win.queue_widget._delegate._theme, "light")

        # Clean up
        win.close()

    def test_sidebar_layout_and_stats(self):
        from PySide6.QtWidgets import QSplitter
        win = MainWindow()
        win.show()

        # Check splitter handle width and window margin spacing
        self.assertEqual(win.centralWidget().layout().contentsMargins().left(), 12)
        splitter = win.findChild(QSplitter)
        self.assertIsNotNone(splitter)
        self.assertEqual(splitter.handleWidth(), 12)

        # Check stats updates
        win.stats.start_session(5)
        win.stats.record_done(1000, 500)
        win.stats.set_working(2)
        self.assertIn("500.0 B", win.stats._v_saved.text())
        self.assertEqual(win.stats._v_files.text(), "1 / 5")

        # Check perf widget worker indicators
        win.perf.update_workers(2, 4, 1)
        self.assertEqual(win.perf._val_gpu.text(), "2")
        self.assertEqual(win.perf._val_cpu.text(), "4")
        self.assertEqual(win.perf._val_que.text(), "1")

        win.close()


if __name__ == "__main__":
    unittest.main()
