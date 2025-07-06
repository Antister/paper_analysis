import sys
import logging
import subprocess

from src.python import main

BUILD_DIR = "build"


def entry() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("[Startup]")

    logger.info("Building native extensions")

    # Config cmake
    ret = subprocess.run(
        [
            "cmake",
            "-S src/cpp",
            "-B " + BUILD_DIR,
            "-G Ninja",
            "-DCMAKE_INSTALL_PREFIX=.",
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    if ret.returncode:
        logger.error(f"CMake configure process failed with {ret.returncode}")

    # Build and install the cpp extension
    ret = subprocess.run(
        [
            "ninja",
            "-C" + BUILD_DIR,
            "install",
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    if ret.returncode:
        logger.error(f"Build process failed with {ret.returncode}")

    # Add library path to python lookup path
    sys.path.append(main.CACHE_DIR)

    # Jump to main
    main.main()


if __name__ == "__main__":
    entry()
