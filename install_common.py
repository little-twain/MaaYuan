import json
import shutil
import sys
from pathlib import Path

from configure import configure_ocr_model


WORKING_DIR = Path(__file__).resolve().parent
INSTALL_PATH = WORKING_DIR / "install"

_DEPENDENCY_INSTALLERS = {
    "win32": "install-deps-win.bat",
    "darwin": "install-deps-mac.sh",
    "linux": "install-deps-linux.sh",
}

_AGENT_EXECUTABLES = {
    "win32": "{PROJECT_DIR}/python/python.exe",
    "darwin": "{PROJECT_DIR}/python/bin/python3",
    "linux": "python3",
}


def get_version(default: str = "v0.0.1") -> str:
    arguments = sys.argv[1:]
    if len(arguments) > 1:
        raise SystemExit("Usage: python <install-script>.py [version]")
    return arguments[0] if arguments and arguments[0].strip() else default


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def _replace_tree(source: Path, destination: Path) -> None:
    _remove_path(destination)
    shutil.copytree(source, destination)


def reset_generated_output() -> None:
    """Remove generated files while preserving embedded Python in release builds."""
    for name in ("resource", "config", "agent", "interface.json"):
        _remove_path(INSTALL_PATH / name)


def install_framework() -> None:
    framework_bin = WORKING_DIR / "deps" / "bin"
    agent_binaries = WORKING_DIR / "deps" / "share" / "MaaAgentBinary"
    if not framework_bin.is_dir() or not agent_binaries.is_dir():
        print('Please download MaaFramework to "deps" first.')
        print('请先下载 MaaFramework 到 "deps"。')
        raise SystemExit(1)

    shutil.copytree(
        framework_bin,
        INSTALL_PATH,
        ignore=shutil.ignore_patterns(
            "*MaaDbgControlUnit*",
            "*MaaThriftControlUnit*",
            "*MaaRpc*",
            "*MaaHttp*",
        ),
        dirs_exist=True,
    )
    shutil.copytree(
        agent_binaries,
        INSTALL_PATH / "MaaAgentBinary",
        dirs_exist_ok=True,
    )


def install_resource(version: str) -> None:
    configure_ocr_model()
    _replace_tree(WORKING_DIR / "assets" / "resource", INSTALL_PATH / "resource")

    source_interface = WORKING_DIR / "assets" / "interface.json"
    with source_interface.open("r", encoding="utf-8") as file:
        interface = json.load(file)
    interface["version"] = version

    INSTALL_PATH.mkdir(parents=True, exist_ok=True)
    destination_interface = INSTALL_PATH / "interface.json"
    with destination_interface.open("w", encoding="utf-8") as file:
        json.dump(interface, file, ensure_ascii=False, indent=4)
        file.write("\n")


def install_chores() -> None:
    INSTALL_PATH.mkdir(parents=True, exist_ok=True)
    for filename in (
        "README.md",
        "LICENSE",
        "自定义派遣脚本修改说明.md",
        "requirements.txt",
    ):
        shutil.copy2(WORKING_DIR / filename, INSTALL_PATH / filename)

    config_path = INSTALL_PATH / "config"
    shutil.copytree(WORKING_DIR / "assets" / "presets", config_path)
    default_preset = WORKING_DIR / "assets" / "presets" / "mfa_新版全部功能.json"
    shutil.copy2(default_preset, config_path / "config.json")

    dependency_installer = _DEPENDENCY_INSTALLERS.get(sys.platform)
    if dependency_installer is not None:
        shutil.copy2(
            WORKING_DIR / dependency_installer,
            INSTALL_PATH / dependency_installer,
        )


def install_agent() -> None:
    _replace_tree(WORKING_DIR / "agent", INSTALL_PATH / "agent")

    interface_path = INSTALL_PATH / "interface.json"
    with interface_path.open("r", encoding="utf-8") as file:
        interface = json.load(file)

    child_executable = _AGENT_EXECUTABLES.get(sys.platform)
    if child_executable is None:
        raise SystemExit(f"Unsupported platform: {sys.platform}")

    agent_settings = interface.setdefault("agent", {})
    agent_settings["child_exec"] = child_executable
    agent_settings["child_args"] = ["{PROJECT_DIR}/agent/main.py", "-u"]

    with interface_path.open("w", encoding="utf-8") as file:
        json.dump(interface, file, ensure_ascii=False, indent=4)
        file.write("\n")


def build_package(version: str, *, include_framework: bool = False) -> None:
    reset_generated_output()
    INSTALL_PATH.mkdir(parents=True, exist_ok=True)
    if include_framework:
        install_framework()
    install_resource(version)
    install_chores()
    install_agent()
