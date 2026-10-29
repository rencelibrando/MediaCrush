#!/usr/bin/env python3
import glob
import io
import os
import sys
import zipfile

def find_cache_root():
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".cache", "JetBrains", "Kotlin", ".m2.cache"),
        os.path.join(home, ".cache", "JetBrains", "Kotlin"),
        os.path.join(home, "Library", "Caches", "JetBrains", "Kotlin", ".m2.cache"),
        os.path.join(home, "Library", "Caches", "JetBrains", "Kotlin"),
    ]
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        candidates.append(os.path.join(user_profile, ".cache", "JetBrains", "Kotlin", ".m2.cache"))
        candidates.append(os.path.join(user_profile, ".cache", "JetBrains", "Kotlin"))

    for path in candidates:
        if os.path.isdir(path):
            return path
    return None

def collect_largest_jars(cache_root):
    jars = {}
    if not cache_root or not os.path.isdir(cache_root):
        return jars

    for root, _, files in os.walk(cache_root):
        for name in files:
            if name.endswith(".jar") and not name.endswith("-sources.jar"):
                path = os.path.join(root, name)
                size = os.path.getsize(path)
                if name not in jars or size > jars[name][0]:
                    jars[name] = (size, path)
    return jars

def build_fat_jar(input_jar_path, output_jar_path):
    print(f"Repackaging {input_jar_path} -> {output_jar_path}")
    cache_root = find_cache_root()
    real_jars = collect_largest_jars(cache_root)

    os.makedirs(os.path.dirname(os.path.abspath(output_jar_path)), exist_ok=True)
    seen_entries = set()

    with zipfile.ZipFile(input_jar_path, "r") as in_z, zipfile.ZipFile(output_jar_path, "w", compression=zipfile.ZIP_DEFLATED) as out_z:
        # Extract BOOT-INF/classes into root
        for info in in_z.infolist():
            if info.filename.startswith("BOOT-INF/classes/") and not info.is_dir():
                rel_path = info.filename[len("BOOT-INF/classes/"):]
                if rel_path not in seen_entries:
                    seen_entries.add(rel_path)
                    out_z.writestr(rel_path, in_z.read(info.filename))

        # Extract BOOT-INF/lib jars into root
        for info in in_z.infolist():
            if info.filename.startswith("BOOT-INF/lib/") and info.filename.endswith(".jar"):
                jar_name = os.path.basename(info.filename)
                jar_bytes = in_z.read(info.filename)

                # Swap out empty stub jars with real ones from cache if available
                if jar_name in real_jars and real_jars[jar_name][0] > len(jar_bytes) + 1024:
                    print(f"Replacing stub {jar_name} ({len(jar_bytes)} bytes) with cached ({real_jars[jar_name][0]} bytes)")
                    with open(real_jars[jar_name][1], "rb") as rf:
                        jar_bytes = rf.read()

                try:
                    with zipfile.ZipFile(io.BytesIO(jar_bytes)) as nested_z:
                        for n_info in nested_z.infolist():
                            if n_info.is_dir():
                                continue
                            if n_info.filename.startswith("META-INF/"):
                                if not n_info.filename.startswith("META-INF/services/"):
                                    continue
                            if n_info.filename not in seen_entries:
                                seen_entries.add(n_info.filename)
                                out_z.writestr(n_info.filename, nested_z.read(n_info.filename))
                except Exception as ex:
                    print(f"Warning: failed unpacking nested jar {jar_name}: {ex}")

        # Set standard root main-class
        manifest = "Manifest-Version: 1.0\nMain-Class: org.example.project.MainKt\n\n"
        out_z.writestr("META-INF/MANIFEST.MF", manifest)

    size_mb = os.path.getsize(output_jar_path) / (1024 * 1024)
    print(f"Successfully generated {output_jar_path} ({size_mb:.2f} MB)")

def main():
    target_in = None
    candidates = glob.glob("build/**/desktopApp-jvm-executable.jar", recursive=True)
    if candidates:
        target_in = candidates[0]

    if not target_in or not os.path.isfile(target_in):
        print("Error: desktopApp-jvm-executable.jar not found under build directory")
        sys.exit(1)

    target_out = os.path.join("dist-input", "mediacrush.jar")
    build_fat_jar(target_in, target_out)

if __name__ == "__main__":
    main()

