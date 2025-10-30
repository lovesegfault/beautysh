"""Allow beautysh to be run as a module with python -m beautysh."""

import sys

from beautysh.cli import BeautyshCLI


def main():
    """Entry point for console script and module execution."""
    cli = BeautyshCLI()
    sys.exit(cli.main(sys.argv[1:]))


if __name__ == "__main__":
    main()
