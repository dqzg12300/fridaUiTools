from pathlib import Path
import os
import sys

from PyInstaller.__main__ import run


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
    for relative_path in DATA_DIRS:
        source = ROOT / relative_path
        options.append(f"--add-data={source}{sep}{relative_path}")
    return options


def main():
    os.chdir(ROOT)
    run(build_options())
    print(f"Build finished: {ROOT / 'dist' / APP_NAME}")


if __name__ == "__main__":
    sys.exit(main())
