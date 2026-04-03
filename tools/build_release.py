from pathlib import Path
import os
import sys

from PyInstaller.__main__ import run
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs


ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "fridaUiTools"
DATA_DIRS = [
    "config",
    "custom",
    "exec",
    "forms",
    "js",
    "lib",
    "sh",
    "ui",
]
HIDDEN_IMPORTS = [
    "capstone",
    "keystone",
    "frida",
]
RUNTIME_PACKAGES = [
    "capstone",
    "keystone",
]


def collect_project_data_files():
    options = []
    seen_files = set()
    sep = ";" if os.name == "nt" else ":"
    for relative_dir in DATA_DIRS:
        source_dir = ROOT / relative_dir
        if source_dir.exists() is False:
            continue
        for file_path in sorted(source_dir.rglob("*")):
            if file_path.is_file() is False:
                continue
            relative_target = file_path.relative_to(ROOT).parent.as_posix()
            item = (str(file_path), relative_target)
            if item in seen_files:
                continue
            seen_files.add(item)
            options.append(f"--add-data={file_path}{sep}{relative_target}")
    return options


def collect_runtime_assets():
    options = []
    seen_dynamic_libs = set()
    seen_data_files = set()
    sep = ";" if os.name == "nt" else ":"
    for package_name in RUNTIME_PACKAGES:
        for source, target in collect_dynamic_libs(package_name):
            item = (source, target)
            if item in seen_dynamic_libs:
                continue
            seen_dynamic_libs.add(item)
            options.append(f"--add-binary={source}{sep}{target}")
        for source, target in collect_data_files(package_name):
            item = (source, target)
            if item in seen_data_files:
                continue
            seen_data_files.add(item)
            options.append(f"--add-data={source}{sep}{target}")
    return options


def build_options():
    sep = ";" if os.name == "nt" else ":"
    options = [
        "--noconfirm",
        "--clean",
        "--windowed",
        f"--name={APP_NAME}",
        f"--paths={ROOT}",
        "--exclude-module=tkinter",
        str(ROOT / "kmainForm.py"),
    ]
    for import_name in HIDDEN_IMPORTS:
        options.append(f"--hidden-import={import_name}")
    options.extend(collect_project_data_files())
    options.extend(collect_runtime_assets())
    return options


def main():
    os.chdir(ROOT)
    run(build_options())
    print(f"Build finished: {ROOT / 'dist' / APP_NAME}")


if __name__ == "__main__":
    sys.exit(main())
