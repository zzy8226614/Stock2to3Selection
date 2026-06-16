import requests
import threading
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "http://127.0.0.1:8000"
ENDPOINTS = [
    ("/api/v1/screen/market-signal", {"trade_date": None, "use_demo_on_failure": True, "force_refresh": False}),
    ("/api/v1/screen/first-board", {"trade_date": None, "use_demo_on_failure": True, "force_refresh": False}),
    ("/api/v1/screen/weak-to-strong", {"trade_date": None, "use_demo_on_failure": True, "force_refresh": False}),
    ("/api/v1/screen/top5", {"trade_date": None, "use_demo_on_failure": True, "force_refresh": False}),
]
HEADERS = {"X-Client-Type": "web-desktop"}

DURATION_SECONDS = 180
CONCURRENCY = 12

lock = threading.Lock()
latencies = []
errors = []
status_counts = {}
health_failures = []
stop_flag = False


def record_status(code):
    with lock:
        status_counts[code] = status_counts.get(code, 0) + 1


def worker():
    idx = 0
    local_count = 0
    while not stop_flag:
        path, payload = ENDPOINTS[idx % len(ENDPOINTS)]
        idx += 1
        url = BASE + path
        t0 = time.perf_counter()
        try:
            r = requests.post(url, json=payload, headers=HEADERS, timeout=35)
            dt = (time.perf_counter() - t0) * 1000
            with lock:
                latencies.append(dt)
            record_status(r.status_code)
            if r.status_code >= 500:
                with lock:
                    errors.append(f"HTTP {r.status_code} {path}")
        except Exception as e:
            dt = (time.perf_counter() - t0) * 1000
            with lock:
                latencies.append(dt)
                errors.append(f"EXC {path}: {type(e).__name__}: {e}")
        local_count += 1
    return local_count


def health_checker():
    while not stop_flag:
        try:
            r = requests.get(BASE + "/api/v1/health", timeout=5)
            if r.status_code != 200:
                with lock:
                    health_failures.append(f"health status {r.status_code}")
        except Exception as e:
            with lock:
                health_failures.append(f"health exc {type(e).__name__}: {e}")
        time.sleep(2)


def pct(values, p):
    if not values:
        return 0.0
    sorted_values = sorted(values)
    k = int(round((p / 100.0) * (len(sorted_values) - 1)))
    return sorted_values[k]


def main():
    global stop_flag
    health_thread = threading.Thread(target=health_checker, daemon=True)
    health_thread.start()

    start = time.time()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = [pool.submit(worker) for _ in range(CONCURRENCY)]
        while time.time() - start < DURATION_SECONDS:
            time.sleep(1)
        stop_flag = True
        counts = [f.result() for f in as_completed(futures)]

    elapsed = time.time() - start
    print("=== Load Test Summary ===")
    print(f"duration_s={elapsed:.1f}")
    print(f"concurrency={CONCURRENCY}")
    print(f"total_requests={sum(counts)}")
    print(f"total_samples={len(latencies)}")
    print(f"errors={len(errors)}")
    print(f"health_failures={len(health_failures)}")
    print(f"status_counts={status_counts}")
    if latencies:
        print(f"latency_ms_p50={pct(latencies, 50):.1f}")
        print(f"latency_ms_p90={pct(latencies, 90):.1f}")
        print(f"latency_ms_p95={pct(latencies, 95):.1f}")
        print(f"latency_ms_p99={pct(latencies, 99):.1f}")
        print(f"latency_ms_avg={statistics.mean(latencies):.1f}")
    if errors:
        print("--- sample errors (up to 15) ---")
        for msg in errors[:15]:
            print(msg)
    if health_failures:
        print("--- health check failures (up to 15) ---")
        for msg in health_failures[:15]:
            print(msg)


if __name__ == "__main__":
    main()
