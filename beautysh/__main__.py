"""Allow beautysh to be run as a module with python -m beautysh."""

import logging
import sys

from beautysh.cli import BeautyshCLI


def main() -> None:
    """Entry point for console script and module execution."""
    logging.basicConfig(
        level=logging.WARNING,
        format="%(name)s - %(levelname)s: %(message)s",
    )
    cli = BeautyshCLI()
    sys.exit(cli.main(sys.argv[1:]))


if __name__ == "__main__":
    main()
