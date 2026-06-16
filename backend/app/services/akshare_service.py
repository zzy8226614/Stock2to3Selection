from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError, as_completed
from zoneinfo import ZoneInfo

from ..runtime_env import sanitize_proxy_environment

sanitize_proxy_environment()

import akshare as ak
import httpx
import pandas as pd
import re

from .cache_service import JsonCacheService

CN_TZ = ZoneInfo("Asia/Shanghai")


def _cn_now() -> datetime:
    return datetime.now(CN_TZ)


def _normalize_trade_date(trade_date: str | None) -> tuple[str, str]:
    if trade_date:
        cleaned = trade_date.replace("-", "")
    else:
        cleaned = _cn_now().strftime("%Y%m%d")
    pretty = f"{cleaned[0:4]}-{cleaned[4:6]}-{cleaned[6:8]}"
    return cleaned, pretty


@dataclass
class MarketDataset:
    trade_date: str
    source: str
    limit_up_pool: pd.DataFrame
    previous_limit_up_pool: pd.DataFrame
    board_snapshot: pd.DataFrame


@dataclass
class MarketOverviewSnapshot:
    market_overview: str
    turnover_overview: str
    notes: list[str]
    has_valid_close: bool


class AkshareDataService:
    def __init__(
        self,
        cache_service: JsonCacheService | None = None,
        max_retries: int = 1,
        fetch_timeout_seconds: float = 8.0,
    ) -> None:
        self.cache_service = cache_service or JsonCacheService()
        self.max_retries = max_retries
        self._memory_cache: dict[str, pd.DataFrame] = {}
        self.fetch_timeout_seconds = fetch_timeout_seconds
        self._fetch_executor = ThreadPoolExecutor(max_workers=8)

    def _fetch_with_timeout(
        self,
        fetcher: Callable[[], pd.DataFrame],
        timeout_seconds: float | None = None,
    ) -> pd.DataFrame:
        effective_timeout = timeout_seconds or self.fetch_timeout_seconds
        future = self._fetch_executor.submit(fetcher)
        try:
            return future.result(timeout=effective_timeout)
        except FutureTimeoutError as exc:
            future.cancel()
            raise TimeoutError(
                f"Akshare fetch timeout after {effective_timeout:.1f}s"
            ) from exc

    def _run_with_cache(
        self,
        cache_key: str,
        fetcher: Callable[[], pd.DataFrame],
        force_refresh: bool = False,
        allow_live_fetch: bool = True,
        timeout_seconds: float | None = None,
    ) -> tuple[pd.DataFrame, str]:
        if not force_refresh:
            in_memory = self._memory_cache.get(cache_key)
            if in_memory is not None:
                return in_memory.copy(deep=False), "cache"
            cached = self.cache_service.load(cache_key)
            if cached is not None:
                frame = pd.DataFrame(cached)
                self._memory_cache[cache_key] = frame
                return frame.copy(deep=False), "cache"

        if not allow_live_fetch:
            return pd.DataFrame(), "empty"

        last_error: Exception | None = None
        for _ in range(self.max_retries):
            try:
                frame = self._fetch_with_timeout(fetcher, timeout_seconds=timeout_seconds)
                if frame is not None and not frame.empty:
                    records = frame.to_dict(orient="records")
                    self.cache_service.save(cache_key, records)
                    self._memory_cache[cache_key] = frame
                    return frame.copy(deep=False), "live"
            except Exception as exc:  # pragma: no cover - network dependent
                last_error = exc

        cached = self.cache_service.load(cache_key)
        if cached is not None:
            frame = pd.DataFrame(cached)
            self._memory_cache[cache_key] = frame
            return frame.copy(deep=False), "cache"

        if last_error is not None:
            raise last_error
        return pd.DataFrame(), "empty"

    def get_market_dataset(
        self,
        trade_date: str | None = None,
        force_refresh: bool = False,
        include_board_snapshot: bool = True,
    ) -> MarketDataset:
        compact_date, pretty_date = _normalize_trade_date(trade_date)
        limit_up_pool, limit_up_source = self._run_with_cache(
            f"limit_up_pool_{compact_date}",
            lambda: ak.stock_zt_pool_em(date=compact_date),
            force_refresh=force_refresh,
        )
        previous_limit_up_pool, previous_source = self._run_with_cache(
            f"previous_limit_up_pool_{compact_date}",
            lambda: ak.stock_zt_pool_previous_em(date=compact_date),
            force_refresh=force_refresh,
        )
        if include_board_snapshot:
            try:
                board_snapshot, board_source = self._run_with_cache(
                    f"industry_board_snapshot_{compact_date}",
                    lambda: ak.stock_board_industry_name_em(),
                    force_refresh=force_refresh,
                )
            except Exception:  # pragma: no cover - network dependent
                board_snapshot, board_source = pd.DataFrame(), "empty"
        else:
            board_snapshot, board_source = pd.DataFrame(), "empty"

        source = ",".join(
            sorted({limit_up_source, previous_source, board_source} - {"empty"}) or {"empty"}
        )
        return MarketDataset(
            trade_date=pretty_date,
            source=source,
            limit_up_pool=limit_up_pool,
            previous_limit_up_pool=previous_limit_up_pool,
            board_snapshot=board_snapshot,
        )

    def get_stock_history(
        self,
        symbol: str,
        trade_date: str | None = None,
        force_refresh: bool = False,
        allow_live_fetch: bool = True,
    ) -> pd.DataFrame:
        compact_date, _ = _normalize_trade_date(trade_date)
        cache_key = f"hist_{symbol}_{compact_date}"

        def fetcher() -> pd.DataFrame:
            return ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date="20230101",
                end_date=compact_date,
                adjust="qfq",
            )

        try:
            frame, _ = self._run_with_cache(
                cache_key,
                fetcher,
                force_refresh=force_refresh,
                allow_live_fetch=allow_live_fetch,
            )
        except Exception:
            frame, _ = self._run_with_cache(
                cache_key,
                lambda: self._fetch_tencent_stock_history(symbol, compact_date),
                force_refresh=True,
                allow_live_fetch=allow_live_fetch,
                timeout_seconds=max(self.fetch_timeout_seconds, 8.0),
            )
        return frame

    def _fetch_tencent_stock_history(self, symbol: str, compact_date: str) -> pd.DataFrame:
        market_symbol = f"sh{symbol}" if symbol.startswith(("6", "9")) else f"sz{symbol}"
        start_date = "20230101"
        params = {
            "param": (
                f"{market_symbol},day,"
                f"{start_date[0:4]}-{start_date[4:6]}-{start_date[6:8]},"
                f"{compact_date[0:4]}-{compact_date[4:6]}-{compact_date[6:8]},640,qfq"
            )
        }
        with httpx.Client(
            timeout=max(self.fetch_timeout_seconds, 8.0),
            headers={"User-Agent": "Mozilla/5.0"},
            verify=False,
            trust_env=False,
        ) as client:
            response = client.get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get", params=params)
            response.raise_for_status()
            payload = response.json()
        stock_payload = payload.get("data", {}).get(market_symbol, {})
        rows = stock_payload.get("qfqday") or stock_payload.get("day") or []
        records: list[dict[str, object]] = []
        for row in rows:
            if len(row) < 6:
                continue
            open_price = self._safe_float(row[1])
            close_price = self._safe_float(row[2])
            high_price = self._safe_float(row[3])
            low_price = self._safe_float(row[4])
            volume_hands = self._safe_float(row[5])
            average_price = (open_price + close_price + high_price + low_price) / 4
            records.append(
                {
                    "日期": row[0],
                    "股票代码": symbol,
                    "开盘": open_price,
                    "收盘": close_price,
                    "最高": high_price,
                    "最低": low_price,
                    "成交量": volume_hands,
                    "成交额": volume_hands * 100 * average_price,
                }
            )
        return pd.DataFrame(records)

    @staticmethod
    def _safe_float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def get_limit_down_pool(self, trade_date: str | None = None, force_refresh: bool = False) -> pd.DataFrame:
        compact_date, _ = _normalize_trade_date(trade_date)
        frame, _ = self._run_with_cache(
            f"limit_down_pool_{compact_date}",
            lambda: ak.stock_zt_pool_dtgc_em(date=compact_date),
            force_refresh=force_refresh,
        )
        return frame

    def get_market_overview(
        self,
        trade_date: str | None = None,
        force_refresh: bool = False,
    ) -> MarketOverviewSnapshot:
        compact_date, pretty_date = _normalize_trade_date(trade_date)
        now = _cn_now()
        is_today = pretty_date == now.strftime("%Y-%m-%d")
        # For today's request before market close, do not backfill yesterday's close.
        if is_today and now.hour < 15:
            return MarketOverviewSnapshot(
                market_overview="当日尚未收盘，暂无可用指数收盘数据。",
                turnover_overview="当日尚未收盘，暂无可用沪深京成交额收盘数据。",
                notes=["交易日未收盘，已停止使用昨日缓存/历史数据回填。"],
                has_valid_close=False,
            )

        notes: list[str] = []
        snapshots: list[dict[str, float | str]] = []
        cached_indexes: list[str] = []
        index_defs = (
            ("沪指", "sh000001"),
            ("深成指", "sz399001"),
            ("创业板指", "sz399006"),
        )
        # Keep close-to-realtime requests responsive after close by capping per-source waits.
        index_timeout = max(self.fetch_timeout_seconds, 12.0)
        with ThreadPoolExecutor(max_workers=len(index_defs)) as executor:
            future_map = {
                executor.submit(
                    self._run_with_cache,
                    f"index_daily_tx_{symbol}_{compact_date}",
                    (lambda symbol=symbol: ak.stock_zh_index_daily_tx(symbol=symbol)),
                    force_refresh,
                    True,
                    index_timeout,
                ): (display_name, symbol)
                for display_name, symbol in index_defs
            }
            for future in as_completed(future_map):
                display_name, _ = future_map[future]
                try:
                    index_frame, source = future.result()
                except Exception:  # pragma: no cover - network dependent
                    continue
                if source == "cache":
                    cached_indexes.append(display_name)
                snapshot = self._extract_index_snapshot(index_frame, pretty_date, display_name)
                if snapshot is not None:
                    snapshots.append(snapshot)

        if cached_indexes:
            notes.append(f"部分指数行情来自本地缓存：{'、'.join(cached_indexes)}。")
        if len(snapshots) < 3:
            fallback_snapshots = self._fetch_tencent_index_snapshots(pretty_date)
            if fallback_snapshots:
                known_names = {str(snapshot.get("name")) for snapshot in snapshots}
                snapshots.extend(
                    snapshot
                    for snapshot in fallback_snapshots
                    if str(snapshot.get("name")) not in known_names
                )
                notes.append("指数行情主接口不可用，已切换腾讯指数日线后备源。")
            else:
                notes.append("部分指数行情获取失败，已使用可用指数样本继续生成情绪信号。")

        market_overview = self._format_index_overview(snapshots)
        turnover_overview = self._format_total_turnover_overview(pretty_date, force_refresh=force_refresh)
        if turnover_overview != "成交额暂不可用。":
            notes.append("成交额采用沪深京总成交额口径。")
        else:
            fallback_turnover = self._format_eastmoney_index_turnover_overview(pretty_date)
            if fallback_turnover != "成交额暂不可用。":
                turnover_overview = fallback_turnover
                notes.append("成交额主接口不可用，已切换腾讯沪深指数成交额后备口径。")
            else:
                notes.append("成交额主口径暂不可用，未展示非同口径降级值。")
        if market_overview == "指数行情暂不可用。" and turnover_overview == "成交额暂不可用。":
            notes.append("指数行情暂不可用，已仅基于涨停/跌停/连板指标生成情绪信号。")
        return MarketOverviewSnapshot(
            market_overview=market_overview,
            turnover_overview=turnover_overview,
            notes=notes,
            has_valid_close=bool(snapshots),
        )

    @staticmethod
    def _extract_index_snapshot(
        index_frame: pd.DataFrame,
        trade_date: str,
        display_name: str,
    ) -> dict[str, float | str] | None:
        if index_frame.empty or "date" not in index_frame.columns:
            return None
        frame = index_frame.copy()
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        frame = frame.dropna(subset=["date"]).sort_values("date")
        if frame.empty:
            return None
        target_date = pd.Timestamp(trade_date)
        exact_day = frame[frame["date"] == target_date]
        if exact_day.empty:
            return None
        current_idx = exact_day.index[-1]
        current_pos = frame.index.get_loc(current_idx)
        if current_pos == 0:
            return None
        current_row = frame.iloc[current_pos]
        previous_row = frame.iloc[current_pos - 1]
        close_price = pd.to_numeric(current_row.get("close"), errors="coerce")
        prev_close = pd.to_numeric(previous_row.get("close"), errors="coerce")
        amount = pd.to_numeric(current_row.get("amount"), errors="coerce")
        prev_amount = pd.to_numeric(previous_row.get("amount"), errors="coerce")
        if pd.isna(close_price) or pd.isna(prev_close) or prev_close <= 0:
            return None
        pct_change = (close_price / prev_close - 1) * 100
        amount_change = 0.0
        if not pd.isna(amount) and not pd.isna(prev_amount):
            amount_change = float(amount - prev_amount)
        return {
            "name": display_name,
            "pct_change": float(pct_change),
            "amount": float(amount) if not pd.isna(amount) else 0.0,
            "amount_change": amount_change,
        }

    def _fetch_tencent_index_snapshots(self, trade_date: str) -> list[dict[str, float | str]]:
        index_defs = (
            ("沪指", "sh000001"),
            ("深成指", "sz399001"),
            ("创业板指", "sz399006"),
        )
        snapshots: list[dict[str, float | str]] = []
        for display_name, symbol in index_defs:
            try:
                frame = self._fetch_tencent_index_history(symbol, trade_date)
            except Exception:
                continue
            snapshot = self._extract_tencent_index_snapshot(frame, trade_date, display_name)
            if snapshot is not None:
                snapshots.append(snapshot)
        return snapshots

    def _fetch_tencent_index_history(self, symbol: str, trade_date: str) -> pd.DataFrame:
        start_date = "2023-01-01"
        params = {"param": f"{symbol},day,{start_date},{trade_date},800,qfq"}
        with httpx.Client(
            timeout=max(self.fetch_timeout_seconds, 8.0),
            headers={"User-Agent": "Mozilla/5.0"},
            verify=False,
            trust_env=False,
        ) as client:
            response = client.get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get", params=params)
            response.raise_for_status()
            payload = response.json()
        rows = payload.get("data", {}).get(symbol, {}).get("qfqday")
        if rows is None:
            rows = payload.get("data", {}).get(symbol, {}).get("day") or []
        return pd.DataFrame(rows, columns=["date", "open", "close", "high", "low", "volume"])

    @staticmethod
    def _extract_tencent_index_snapshot(
        index_frame: pd.DataFrame,
        trade_date: str,
        display_name: str,
    ) -> dict[str, float | str] | None:
        if index_frame.empty or "date" not in index_frame.columns:
            return None
        frame = index_frame.copy()
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        frame = frame.dropna(subset=["date"]).sort_values("date")
        target_date = pd.Timestamp(trade_date)
        exact_day = frame[frame["date"] == target_date]
        if exact_day.empty:
            return None
        current_idx = exact_day.index[-1]
        current_pos = frame.index.get_loc(current_idx)
        if current_pos == 0:
            return None
        current_row = frame.iloc[current_pos]
        previous_row = frame.iloc[current_pos - 1]
        close_price = pd.to_numeric(current_row.get("close"), errors="coerce")
        prev_close = pd.to_numeric(previous_row.get("close"), errors="coerce")
        if pd.isna(close_price) or pd.isna(prev_close) or prev_close <= 0:
            return None
        return {
            "name": display_name,
            "pct_change": float((close_price / prev_close - 1) * 100),
            "amount": 0.0,
            "amount_change": 0.0,
        }

    def _format_eastmoney_index_turnover_overview(self, trade_date: str) -> str:
        if trade_date != _cn_now().strftime("%Y-%m-%d"):
            return "成交额暂不可用。"
        try:
            with httpx.Client(
                timeout=max(self.fetch_timeout_seconds, 8.0),
                headers={"User-Agent": "Mozilla/5.0"},
                verify=False,
                trust_env=False,
            ) as client:
                response = client.get("https://qt.gtimg.cn/q=sh000001,sz399001")
                response.raise_for_status()
            total_amount = 0.0
            for quote in response.text.splitlines():
                if '"' not in quote:
                    continue
                fields = quote.split('"', 2)[1].split("~")
                if len(fields) > 37:
                    # Tencent field 37 is amount in 10k CNY for index quotes.
                    total_amount += self._safe_float(fields[37]) * 10_000
            if total_amount <= 0:
                return "成交额暂不可用。"
            return f"{total_amount / 1_000_000_000_000:.2f}万亿"
        except Exception:
            return "成交额暂不可用。"

    def _format_total_turnover_overview(self, trade_date: str, force_refresh: bool = False) -> str:
        compact_date = trade_date.replace("-", "")
        spot_frame = pd.DataFrame()
        # Avoid long tail latency in degraded windows; fallback to legu quickly.
        attempts = 1 if force_refresh else 2
        for _ in range(attempts):
            try:
                spot_frame, _ = self._run_with_cache(
                    f"a_spot_total_turnover_{compact_date}",
                    lambda: ak.stock_zh_a_spot_em(),
                    force_refresh=force_refresh,
                    timeout_seconds=max(self.fetch_timeout_seconds, 8.0),
                )
                if not spot_frame.empty:
                    break
            except Exception:
                spot_frame = pd.DataFrame()
                continue
        if not spot_frame.empty and "成交额" in spot_frame.columns:
            amount_series = pd.to_numeric(spot_frame["成交额"], errors="coerce").fillna(0)
            total_amount = float(amount_series.sum())
            if total_amount > 0:
                return f"{total_amount / 1_000_000_000_000:.2f}万亿"
        legu_amount = self._read_turnover_from_legu(compact_date, force_refresh=force_refresh)
        if legu_amount > 0:
            return f"{legu_amount / 1_000_000_000_000:.2f}万亿"
        return "成交额暂不可用。"

    def _read_turnover_from_legu(self, compact_date: str, force_refresh: bool = False) -> float:
        try:
            legu_frame, _ = self._run_with_cache(
                f"market_activity_legu_{compact_date}",
                lambda: ak.stock_market_activity_legu(),
                force_refresh=force_refresh,
                timeout_seconds=max(self.fetch_timeout_seconds, 6.0),
            )
        except Exception:
            return 0.0
        if legu_frame.empty or "item" not in legu_frame.columns or "value" not in legu_frame.columns:
            return 0.0
        for _, row in legu_frame.iterrows():
            item_text = str(row.get("item", "")).strip()
            value_text = str(row.get("value", "")).strip()
            if not item_text or not value_text:
                continue
            if "%" in value_text or ":" in value_text:
                continue
            if ("成交额" not in item_text) and ("成交" not in item_text) and ("金额" not in item_text):
                continue
            match = re.search(r"[-+]?\d+(?:\.\d+)?", value_text)
            if not match:
                continue
            numeric = float(match.group(0))
            if "万亿" in value_text:
                return numeric * 1_000_000_000_000
            if "亿" in value_text:
                return numeric * 100_000_000
            return numeric * 100_000_000
        return 0.0

    @staticmethod
    def _format_index_overview(index_snapshots: list[dict[str, float | str]]) -> str:
        if not index_snapshots:
            return "指数行情暂不可用。"
        values: list[str] = []
        for snapshot in index_snapshots:
            display_name = str(snapshot.get("name", "")).strip()
            pct = pd.to_numeric(snapshot.get("pct_change"), errors="coerce")
            if not display_name or pd.isna(pct):
                continue
            values.append(f"{display_name}{pct:+.2f}%")
        return "，".join(values) if values else "指数行情暂不可用。"

    @staticmethod
    def _format_turnover_overview(index_snapshots: list[dict[str, float | str]]) -> str:
        if not index_snapshots:
            return "成交额暂不可用。"
        turnover = sum(
            pd.to_numeric(snapshot.get("amount"), errors="coerce")
            for snapshot in index_snapshots
        )
        turnover_change = sum(
            pd.to_numeric(snapshot.get("amount_change"), errors="coerce")
            for snapshot in index_snapshots
        )
        if pd.isna(turnover) or turnover <= 0:
            return "成交额暂不可用。"
        direction = "放量" if turnover_change >= 0 else "缩量"
        return (
            f"{turnover / 1_000_000_000:.2f}万亿，"
            f"较上个交易日{direction}{abs(turnover_change) / 100_000_000:.2f}亿"
        )
