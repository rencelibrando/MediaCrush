# MediaCrush

High-performance, modern multiplatform media compressor built with **Kotlin Multiplatform (KMP)** and **Compose Multiplatform**.

Targeting **Desktop (Linux, Windows, macOS)**, **Android**, and **iOS**, powered by native hardware encoders (NVENC, VAAPI, AMF, QSV, VideoToolbox) and a custom Supabase-inspired design system.

---

##  Features

- ** Native Hardware Acceleration**:
  - Automatically probes and leverages GPU video encoders: NVIDIA NVENC (`hevc_nvenc`, `h264_nvenc`, `av1_nvenc`), Intel QSV (`hevc_qsv`, `h264_qsv`), AMD AMF (`hevc_amf`, `h264_amf`), Linux VAAPI (`/dev/dri/renderD*`), and Apple VideoToolbox (`hevc_videotoolbox`, `h264_videotoolbox`).
  - Gracefully falls back to high-efficiency CPU encoders (`libx265`, `libx264`, `libsvtav1`).
- ** Non-Blocking Reactive Engine**:
  - Thread-safe, non-blocking rolling buffer reader for FFmpeg `out_time_ms=` progress streaming.
  - Instant pause, resume, per-task cancellation, and queue clearing.
  - Real-time CPU, RAM, and GPU hardware metrics monitor.
- ** Built with Kotlin Toolchain (Amper)**:
  - Built directly using `./kotlin` and `./kotlin.bat` CLI wrappers. No Gradle installation required.
  - Declarative configuration in `project.yaml` and `module.yaml`.

---

##  Project Architecture

```
MediaCrush/
├── .github/workflows/
│   └── release.yml          # Automated multiplatform release pipeline
├── shared/                  # Common multiplatform business logic & UI
│   ├── src/                 # Common Compose UI, state, engine, models, theme
│   ├── src@jvm/             # Desktop JVM actuals (hardware detector, compressors)
│   ├── src@android/         # Android actuals & platform bridge
│   ├── src@ios/             # iOS actuals & platform bridge
│   └── test/                # Unit test suite
├── desktopApp/              # Desktop application launcher (JVM / Compose Desktop)
├── androidApp/              # Android application launcher
├── iosApp/                  # iOS application launcher
├── kotlin                   # Self-bootstrapping Kotlin Toolchain CLI (Linux/macOS)
├── kotlin.bat               # Self-bootstrapping Kotlin Toolchain CLI (Windows)
├── libs.versions.toml       # Pinned dependency catalog
└── project.yaml             # Toolchain project configuration
```

---

## Building & Running Locally

The repository includes self-bootstrapping `./kotlin` wrappers:

```bash
# 1. Run Desktop Application
./kotlin run -m desktopApp

# 2. Run Android Application
./kotlin run -m androidApp

# 3. Run Test Suite
./kotlin test -m shared

# 4. Package Standalone Executable Desktop JAR
./kotlin package -m desktopApp -f executable-jar
```

---

##  Automated CI/CD Release Pipeline

The GitHub Actions workflow [`.github/workflows/release.yml`](.github/workflows/release.yml) automatically builds and publishes ready-to-use binaries on every `v*` tag push or via manual `workflow_dispatch`:

| Target Platform | Package Formats | Output Artifact |
| :--- | :--- | :--- |
| **Linux** | `.deb`, `.rpm` | `mediacrush_*.deb`<br>`mediacrush-*.rpm` |
| **Windows** | `.msi`, `.exe` | `MediaCrush-*.msi`<br>`MediaCrush-*.exe` |
| **macOS** | `.dmg`, `.pkg` | `MediaCrush-*.dmg`<br>`MediaCrush-*.pkg` |
| **Android** | `.apk`, `.aab` | `MediaCrush-Android.apk`<br>`MediaCrush-Android.aab` |

To trigger a release:
```bash
git tag v1.0.0
git push origin v1.0.0
```

---

##  License

MIT License. See [LICENSE](LICENSE) for details.
