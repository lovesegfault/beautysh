# Beautysh Development Tools

This directory contains performance analysis and benchmarking tools for beautysh development.

## Tools

### benchmark.py

Performance benchmarking script that measures formatter throughput across various script sizes.

**Usage:**

```bash
python tools/benchmark.py
```

**Output:**

- Average formatting time per script size
- Throughput (lines/second)
- Benchmarks on real test fixtures

### profile_formatter.py

cProfile-based profiling tool to identify performance hotspots in the formatter.

**Usage:**

```bash
python tools/profile_formatter.py
```

**Output:**

- Top 30 functions by cumulative time
- Top 30 functions by total time
- Caller relationships for expensive functions

Use this to identify bottlenecks when optimizing the formatter.
