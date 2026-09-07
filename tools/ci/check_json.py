import argparse
import json
from pathlib import Path


def validate_file(path: Path) -> None:
    with path.open("r", encoding="utf-8") as file:
        json.load(file)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate UTF-8 JSON files.")
    parser.add_argument("roots", nargs="+", type=Path)
    arguments = parser.parse_args()

    count = 0
    for root in arguments.roots:
        paths = root.rglob("*.json") if root.is_dir() else [root]
        for path in paths:
            try:
                validate_file(path)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
                raise SystemExit(f"{path}: {error}")
            count += 1

    print(f"Validated {count} JSON files.")


if __name__ == "__main__":
    main()
