"""Allow beautysh to be run as a module with python -m beautysh."""

import sys

from beautysh import Beautify


def main():
    """Entry point for console script and module execution."""
    sys.exit(Beautify().main(sys.argv[1:]))


if __name__ == "__main__":
    main()
