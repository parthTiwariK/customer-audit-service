#!/usr/bin/env python3
"""Benchmark customer-audit HTTP API (server time via X-Response-Time).

Usage:
  # Start API first (dev or gunicorn), AUTH_MODE=dev recommended:
  python scripts/benchmark.py --url http://127.0.0.1:8002
  python scripts/benchmark.py --url http://127.0.0.1:8002 --warm 5
"""

from __future__ import annotations

import argparse
import statistics
import time
import urllib.error
import urllib.request

ENDPOINTS = [
    ("health", "/health"),
    ("ready", "/ready"),
    ("audits_search", "/api/v1/audits?page=1&page_size=25"),
    ("questionnaires_latest", "/api/v1/questionnaires/latest"),
    ("reports_summary", "/api/v1/reports/summary"),
]


def fetch(url: str, timeout: float = 60.0) -> dict:
    req = urllib.request.Request(url, headers={"Accept-Encoding": "identity"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            status = resp.status
            headers = resp.headers
    except urllib.error.HTTPError as exc:
        body = exc.read()
        status = exc.code
        headers = exc.headers
    elapsed = time.perf_counter() - t0
    return {
        "total_s": elapsed,
        "size": len(body),
        "status": status,
        "server_time": headers.get("X-Response-Time"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Case Audit API")
    parser.add_argument("--url", default="http://127.0.0.1:8002", help="API base URL")
    parser.add_argument("--warm", type=int, default=1, help="Iterations per endpoint (after 1 cold)")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    print(f"Target: {base}")
    print(f"{'endpoint':<22} {'status':>6} {'bytes':>8} {'server':>12} {'total_s':>10}")
    print("-" * 64)

    for name, path in ENDPOINTS:
        url = base + path
        cold = fetch(url)
        times = [cold["total_s"]]
        server_vals = [cold["server_time"] or ""]
        status = cold["status"]
        size = cold["size"]
        for _ in range(max(0, args.warm - 1)):
            row = fetch(url)
            times.append(row["total_s"])
            if row["server_time"]:
                server_vals.append(row["server_time"])
            status = row["status"]
            size = row["size"]
        warm_total = statistics.mean(times[1:]) if len(times) > 1 else times[0]
        server = server_vals[-1] if server_vals else ""
        label = name if args.warm <= 1 else f"{name} (warm avg)"
        display_s = warm_total if args.warm > 1 else times[0]
        print(
            f"{label:<22} {status:>6} {size:>8} {server or '-':>12} {display_s:>10.4f}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())