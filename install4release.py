from install_common import INSTALL_PATH, build_package, get_version


def main() -> None:
    build_package(get_version())
    print(f"Install to {INSTALL_PATH} successfully.")


if __name__ == "__main__":
    main()
