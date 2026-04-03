import argparse
import shutil
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "fridaUiTools"


def sanitize_version(version: str) -> str:
    version = (version or "").strip()
    if version.startswith("v"):
        return version[1:]
    return version


def create_flat_zip(dist_dir: Path, archive_path: Path):
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(dist_dir.rglob("*")):
            if file_path.is_file() is False:
                continue
            zf.write(file_path, arcname=file_path.relative_to(dist_dir))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--platform", default="")
    parser.add_argument("--format", choices=["zip", "gztar"], default="zip")
    parser.add_argument("--include-platform-in-name", action="store_true")
    args = parser.parse_args()

    dist_dir = ROOT / "dist" / APP_NAME
    if not dist_dir.exists():
        raise FileNotFoundError(f"Build output not found: {dist_dir}")

    version_name = sanitize_version(args.version)
    archive_name = f"{APP_NAME}_{version_name}"
    if args.include_platform_in_name and args.platform:
        archive_name += f"_{args.platform}"

    if args.format == "zip":
        archive_path = ROOT / "dist" / f"{archive_name}.zip"
        create_flat_zip(dist_dir, archive_path)
    else:
        archive_base = ROOT / "dist" / archive_name
        archive_path = Path(shutil.make_archive(str(archive_base), args.format, root_dir=dist_dir, base_dir="."))
    print(str(archive_path))


if __name__ == "__main__":
    main()
