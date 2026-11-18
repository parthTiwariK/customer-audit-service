#!/usr/bin/env python3
"""Concurrent load test for Case Audit API (dev auth: no cookie required)."""

from __future__ import annotations

import argparse
import concurrent.futures
import random
import statistics
import time
import urllib.error
import urllib.request

PATHS = [
    "/health",
    "/api/v1/audits?page=1&page_size=25",
    "/api/v1/reports/summary",
    "/api/v1/questionnaires/latest",
]


def fetch(base: str, path: str, timeout: float) -> tuple[float, int]:
    url = base.rstrip("/") + path
    req = urllib.request.Request(url, headers={"Accept-Encoding": "identity"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()
            return time.perf_counter() - t0, resp.status
    except urllib.error.HTTPError as exc:
        exc.read()
        return time.perf_counter() - t0, exc.code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8002")
    parser.add_argument("--users", type=int, default=20)
    parser.add_argument("--duration", type=int, default=30)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    end = time.time() + args.duration
    latencies: list[float] = []
    errors = 0
    ok = 0

    def worker() -> None:
        nonlocal errors, ok
        while time.time() < end:
            path = random.choice(PATHS)
            elapsed, status = fetch(args.url, path, args.timeout)
            latencies.append(elapsed)
            if status and 200 <= status < 400:
                ok += 1
            else:
                errors += 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.users) as pool:
        futs = [pool.submit(worker) for _ in range(args.users)]
        concurrent.futures.wait(futs)

    total = ok + errors
    print(f"Requests: {total}, errors: {errors}")
    if latencies:
        latencies.sort()
        p95_idx = max(0, int(len(latencies) * 0.95) - 1)
        print(f"p50: {statistics.median(latencies):.3f}s")
        print(f"p95: {latencies[p95_idx]:.3f}s")
        print(f"max: {max(latencies):.3f}s")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())