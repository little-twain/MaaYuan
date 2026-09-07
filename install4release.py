import sys
from pathlib import Path


# The Windows embedded Python uses an isolated sys.path configured by its
# `python._pth` file and may not add this script's directory automatically.
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from install_common import INSTALL_PATH, build_package, get_version


def main() -> None:
    build_package(get_version())
    print(f"Install to {INSTALL_PATH} successfully.")


if __name__ == "__main__":
    main()
