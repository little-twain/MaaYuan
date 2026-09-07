import sys
from pathlib import Path

from maa.resource import Resource
from maa.tasker import LoggingLevelEnum, Tasker


def check(directories: list[Path]) -> bool:
    resource = Resource()

    print(f"Checking {len(directories)} directories...")
    for directory in directories:
        print(f"Checking {directory}...")
        status = resource.post_bundle(directory).wait().status
        if not status.succeeded:
            print(f"Failed to check {directory}.")
            return False

    print("All directories checked.")
    return True


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python check_resource.py <directory> [directory ...]")
        sys.exit(1)

    Tasker.set_stdout_level(LoggingLevelEnum.All)
    directories = [Path(argument) for argument in sys.argv[1:]]
    if not check(directories):
        sys.exit(1)


if __name__ == "__main__":
    main()
