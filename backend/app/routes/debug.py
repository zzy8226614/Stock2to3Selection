from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime
from time import perf_counter
from zoneinfo import ZoneInfo

import akshare as ak
from fastapi import APIRouter, Query

from ..runtime_env import REMOVED_PROXY_ENV, sanitize_proxy_environment

CN_TZ = ZoneInfo("Asia/Shanghai")

router = APIRouter(prefix="/debug", tags=["debug"])


def _run_probe(name: str, fn, timeout_seconds: float) -> dict[str, object]:
    started = perf_counter()
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fn)
    try:
        value = future.result(timeout=timeout_seconds)
        elapsed_ms = int((perf_counter() - started) * 1000)
        return {
            "name": name,
            "ok": True,
            "elapsedMs": elapsed_ms,
            "detail": value,
        }
    except FutureTimeoutError:
        future.cancel()
        elapsed_ms = int((perf_counter() - started) * 1000)
        return {
            "name": name,
            "ok": False,
            "elapsedMs": elapsed_ms,
            "error": f"timeout after {timeout_seconds:.1f}s",
        }
    except Exception as exc:  # pragma: no cover - network dependent
        elapsed_ms = int((perf_counter() - started) * 1000)
        return {
            "name": name,
            "ok": False,
            "elapsedMs": elapsed_ms,
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


@router.get("/upstream-check")
def upstream_check(timeout_seconds: float = Query(default=20.0, ge=3.0, le=90.0)) -> dict[str, object]:
    removed_proxy_env = sanitize_proxy_environment()
    today = datetime.now(CN_TZ).strftime("%Y-%m-%d")

    def probe_index(symbol: str) -> dict[str, object]:
        frame = ak.stock_zh_index_daily_tx(symbol=symbol)
        if frame.empty:
            return {"rows": 0, "todayFound": False}
        frame = frame.copy()
        frame["date"] = frame["date"].astype(str)
        today_rows = frame[frame["date"].str.startswith(today)]
        latest = frame.tail(1).to_dict(orient="records")[0]
        return {"rows": int(len(frame.index)), "todayFound": not today_rows.empty, "latest": latest}

    def probe_spot_turnover() -> dict[str, object]:
        frame = ak.stock_zh_a_spot_em()
        if frame.empty:
            return {"rows": 0, "columns": []}
        columns = list(frame.columns)
        has_turnover_col = "成交额" in columns
        turnover_sample = None
        if has_turnover_col:
            sample_series = frame["成交额"].head(5).astype(str).tolist()
            turnover_sample = sample_series
        return {
            "rows": int(len(frame.index)),
            "columns": columns[:20],
            "hasTurnoverColumn": has_turnover_col,
            "turnoverSample": turnover_sample,
        }

    def probe_legu() -> dict[str, object]:
        frame = ak.stock_market_activity_legu()
        if frame.empty:
            return {"rows": 0, "columns": []}
        preview = frame.head(12).to_dict(orient="records")
        return {
            "rows": int(len(frame.index)),
            "columns": list(frame.columns),
            "preview": preview,
        }

    probes = [
        _run_probe("index_sh000001_daily_tx", lambda: probe_index("sh000001"), timeout_seconds),
        _run_probe("index_sz399001_daily_tx", lambda: probe_index("sz399001"), timeout_seconds),
        _run_probe("index_sz399006_daily_tx", lambda: probe_index("sz399006"), timeout_seconds),
        _run_probe("spot_a_share_turnover", probe_spot_turnover, timeout_seconds),
        _run_probe("market_activity_legu", probe_legu, timeout_seconds),
    ]
    return {
        "success": True,
        "data": {
            "tradeDate": today,
            "timeoutSeconds": timeout_seconds,
            "proxySanitized": bool(REMOVED_PROXY_ENV or removed_proxy_env),
            "probes": probes,
        },
    }
