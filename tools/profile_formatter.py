#!/usr/bin/env python3
"""Profile beautysh formatter to identify performance hotspots."""

import cProfile
import pstats

from beautysh import BashFormatter


def generate_test_script(lines: int = 2000) -> str:
    """Generate a complex test Bash script."""
    script_lines = ["#!/usr/bin/env bash", ""]

    for i in range(lines // 10):
        script_lines.extend(
            [
                f"function test_func_{i}() {{",
                f"    local var{i}=$1",
                f'    if [ -n "$var{i}" ]; then',
                f'        echo "Processing $var{i}"',
                "        for j in $(seq 1 10); do",
                '            case "$j" in',
                "                1|2|3)",
                '                    echo "Small: $j"',
                "                    ;;",
                "                *)",
                '                    echo "Other: $j"',
                "                    ;;",
                "            esac",
                "        done",
                "    fi",
                "}",
                "",
            ]
        )

    return "\n".join(script_lines)


def profile_formatter():
    """Profile the formatter with cProfile."""
    print("=" * 70)
    print("Profiling Beautysh Formatter")
    print("=" * 70)
    print()

    # Generate test script
    script = generate_test_script(2000)
    lines = len(script.split("\n"))
    print(f"Test script: {lines} lines")
    print()

    # Profile the formatter
    formatter = BashFormatter()

    profiler = cProfile.Profile()
    profiler.enable()

    # Run formatter multiple times
    for _ in range(20):
        formatted, error = formatter.beautify_string(script)

    profiler.disable()

    # Print statistics
    print("Top 30 functions by cumulative time:")
    print("=" * 70)
    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats("cumulative")
    stats.print_stats(30)

    print()
    print("=" * 70)
    print("Top 30 functions by total time:")
    print("=" * 70)
    stats.sort_stats("tottime")
    stats.print_stats(30)

    print()
    print("=" * 70)
    print("Callers of expensive functions:")
    print("=" * 70)
    stats.print_callers(10)


if __name__ == "__main__":
    profile_formatter()
