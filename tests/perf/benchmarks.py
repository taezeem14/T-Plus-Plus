from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from tpp.runtime import EngineConfig, RuntimeEngine


@dataclass
class BenchmarkResult:
    name: str
    iterations: int
    total_time_sec: float
    avg_ms: float
    ops_per_sec: float


BENCHMARKS: list[tuple[str, str, int]] = [
    (
        "tight_loop",
        (
            "let x be 0\n"
            "repeat 1000 times:\n"
            "    increase x by 1\n"
        ),
        10,
    ),
    (
        "fibonacci_recursion",
        (
            "define fib with n as:\n"
            "    if n is less than 2:\n"
            "        give back n\n"
            "    give back fib(n - 1) + fib(n - 2)\n"
            "let res be call fib with 12\n"
        ),
        5,
    ),
    (
        "string_operations",
        (
            "let s be \"\"\n"
            "let x be 42\n"
            "repeat 100 times:\n"
            "    let s be \"iter: {x}\"\n"
        ),
        20,
    ),
    (
        "collection_comprehension",
        (
            "let nums be 1 to 100\n"
            "let evens be a list containing x times 2 for each x in nums if x % 2 == 0\n"
        ),
        15,
    ),
]


def run_benchmark_suite() -> list[BenchmarkResult]:
    results: list[BenchmarkResult] = []
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy", optimize=True))

    for name, code, iters in BENCHMARKS:
        # Warmup
        engine.run_source(code)

        start = time.perf_counter()
        for _ in range(iters):
            engine.run_source(code)
        elapsed = time.perf_counter() - start

        avg_ms = (elapsed / iters) * 1000.0
        ops_per_sec = iters / elapsed if elapsed > 0 else float("inf")

        results.append(
            BenchmarkResult(
                name=name,
                iterations=iters,
                total_time_sec=elapsed,
                avg_ms=avg_ms,
                ops_per_sec=ops_per_sec,
            )
        )

    return results


def save_baseline(results: list[BenchmarkResult], output_path: Path) -> None:
    data = {r.name: asdict(r) for r in results}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    res = run_benchmark_suite()
    for r in res:
        print(f"[{r.name}] {r.avg_ms:.2f} ms/run ({r.ops_per_sec:.1f} ops/sec)")
