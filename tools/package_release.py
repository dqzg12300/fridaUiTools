import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "fridaUiTools"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--format", choices=["zip", "gztar"], default="zip")
    args = parser.parse_args()

    dist_dir = ROOT / "dist" / APP_NAME
    if not dist_dir.exists():
        raise FileNotFoundError(f"Build output not found: {dist_dir}")

    archive_base = ROOT / "dist" / f"{APP_NAME}-{args.platform}-{args.version}"
    archive_path = shutil.make_archive(str(archive_base), args.format, root_dir=dist_dir.parent, base_dir=dist_dir.name)
    print(archive_path)


if __name__ == "__main__":
    main()
