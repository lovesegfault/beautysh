#!/usr/bin/env python3
"""Performance benchmark for beautysh formatter.

This script benchmarks the formatter on various script sizes to measure
performance improvements from pattern pre-compilation and other optimizations.
"""

import time
from pathlib import Path

from beautysh import BashFormatter


def generate_test_script(lines: int) -> str:
    """Generate a test Bash script with specified number of lines.

    Args:
        lines: Number of lines to generate

    Returns:
        Generated Bash script
    """
    script_lines = ["#!/usr/bin/env bash", ""]

    # Generate various Bash constructs
    for i in range(lines // 10):
        script_lines.extend(
            [
                f"function test_func_{i}() {{",
                f"    local var{i}=$1",
                f'    if [ -n "$var{i}" ]; then',
                f'        echo "Processing $var{i}"',
                f'        case "$var{i}" in',
                f"            pattern{i})",
                f'                echo "Matched pattern{i}"',
                "                ;;",
                "            *)",
                '                echo "No match"',
                "                ;;",
                "        esac",
                "    fi",
                "}",
                "",
            ]
        )

    return "\n".join(script_lines)


def benchmark_formatter(script: str, iterations: int = 100) -> tuple[float, float]:
    """Benchmark the formatter on a script.

    Args:
        script: Script to format
        iterations: Number of iterations to run

    Returns:
        Tuple of (average_time_ms, total_time_ms)
    """
    formatter = BashFormatter()

    # Warm-up run
    formatter.beautify_string(script)

    # Benchmark runs
    start_time = time.perf_counter()
    for _ in range(iterations):
        formatted, error = formatter.beautify_string(script)
    end_time = time.perf_counter()

    total_time = (end_time - start_time) * 1000  # Convert to ms
    avg_time = total_time / iterations

    return avg_time, total_time


def main():
    """Run benchmarks with different script sizes."""
    print("=" * 70)
    print("Beautysh Performance Benchmark")
    print("=" * 70)
    print()

    test_sizes = [
        (100, 100),  # 100 lines, 100 iterations
        (500, 50),  # 500 lines, 50 iterations
        (1000, 20),  # 1000 lines, 20 iterations
        (5000, 5),  # 5000 lines, 5 iterations
    ]

    results = []

    for lines, iterations in test_sizes:
        print(f"Generating test script with {lines} lines...")
        script = generate_test_script(lines)
        actual_lines = len(script.split("\n"))

        print(f"Running {iterations} iterations...")
        avg_time, total_time = benchmark_formatter(script, iterations)

        lines_per_sec = (actual_lines * iterations) / (total_time / 1000)

        results.append(
            {
                "lines": actual_lines,
                "iterations": iterations,
                "avg_time_ms": avg_time,
                "total_time_ms": total_time,
                "lines_per_sec": lines_per_sec,
            }
        )

        print(f"  Lines: {actual_lines}")
        print(f"  Average time: {avg_time:.3f} ms")
        print(f"  Total time: {total_time:.3f} ms")
        print(f"  Throughput: {lines_per_sec:.0f} lines/sec")
        print()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"{'Lines':<10} {'Iterations':<12} {'Avg Time (ms)':<15} {'Lines/sec':<15}")
    print("-" * 70)
    for result in results:
        print(
            f"{result['lines']:<10} {result['iterations']:<12} "
            f"{result['avg_time_ms']:<15.3f} {result['lines_per_sec']:<15.0f}"
        )
    print()

    # Test with real files if available
    fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
    if fixtures_dir.exists():
        print("=" * 70)
        print("Benchmarking Real Test Fixtures")
        print("=" * 70)
        print()

        for fixture_file in sorted(fixtures_dir.glob("*_raw.sh"))[:5]:
            print(f"File: {fixture_file.name}")
            script = fixture_file.read_text()
            lines = len(script.split("\n"))

            avg_time, total_time = benchmark_formatter(script, iterations=100)
            print(f"  Lines: {lines}")
            print(f"  Average time: {avg_time:.3f} ms")
            print()


if __name__ == "__main__":
    main()
