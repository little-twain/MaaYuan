import shutil

from install_common import INSTALL_PATH, build_package, get_version


def main() -> None:
    if INSTALL_PATH.exists():
        shutil.rmtree(INSTALL_PATH)
    build_package(get_version(), include_framework=True)
    print(f"Install to {INSTALL_PATH} successfully.")


if __name__ == "__main__":
    main()
