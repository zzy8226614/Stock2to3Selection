from __future__ import annotations

from datetime import datetime
import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.akshare_service import MarketDataset, MarketOverviewSnapshot, AkshareDataService
from backend.app.models.schemas import MarketSignalResponse
from backend.app.routes import v1_screening
from backend.app.services.screener_service import ScreenerService

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_v1_health() -> None:
    response = client.get("/api/v1/health", headers={"X-Client-Type": "windows-mfc"})
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["meta"]["clientType"] == "windows-mfc"
    assert response.headers["X-Request-Id"]


def test_first_board_demo_response() -> None:
    response = client.post("/screen/first-board", json={"use_demo_on_failure": True})
    body = response.json()
    assert response.status_code == 200
    assert "trade_date" in body
    assert "market_summary" in body
    assert "items" in body


def test_weak_to_strong_demo_response() -> None:
    response = client.post("/screen/weak-to-strong", json={"use_demo_on_failure": True})
    body = response.json()
    assert response.status_code == 200
    assert isinstance(body["items"], list)


def test_top5_demo_response() -> None:
    response = client.post("/screen/top5", json={"use_demo_on_failure": True})
    body = response.json()
    assert response.status_code == 200
    assert len(body["items"]) <= 5


def test_board_top10_limit_up_demo_response() -> None:
    response = client.post("/screen/board-top10-limit-up", json={"use_demo_on_failure": True})
    body = response.json()
    assert response.status_code == 200
    assert "trade_date" in body
    assert "market_summary" in body
    assert "items" in body


def test_second_board_analysis_response() -> None:
    response = client.post("/screen/second-board-analysis", json={"trade_date": "2099-01-01", "use_demo_on_failure": True})
    body = response.json()
    assert response.status_code == 200
    assert "trade_date" in body
    assert "market_summary" in body
    assert "items" in body


def test_market_signal_response() -> None:
    response = client.post("/screen/market-signal", json={"use_demo_on_failure": True})
    body = response.json()
    assert response.status_code == 200
    assert "trade_date" in body
    assert "regime" in body
    assert "indicators" in body


def test_v1_first_board_response() -> None:
    response = client.post(
        "/api/v1/screen/first-board",
        json={"use_demo_on_failure": True},
        headers={"X-Client-Type": "windows-mfc"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert "data" in body
    assert "meta" in body
    assert body["meta"]["clientType"] == "windows-mfc"
    assert "trade_date" in body["data"]


def test_v1_market_signal_response() -> None:
    response = client.post(
        "/api/v1/screen/market-signal",
        json={"use_demo_on_failure": True},
        headers={"X-Client-Type": "android"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"]["clientType"] == "android"
    assert "regime" in body["data"]


def test_v1_market_signal_meta_marks_degraded_when_overview_unavailable(monkeypatch) -> None:
    def fake_build_market_signal(
        trade_date: str | None,
        use_demo_on_failure: bool,
        force_refresh: bool = False,
    ) -> MarketSignalResponse:
        return MarketSignalResponse(
            trade_date=trade_date or "2026-04-28",
            weekday="星期二",
            marketOverview="指数行情暂不可用。",
            turnoverOverview="成交额暂不可用。",
            regime="YELLOW",
            regimeLabel="黄灯",
            positionAdvice="当日未收盘，建议仅观察，不执行收盘后策略。",
            indicators=[],
            notes=["指数行情暂不可用，已仅基于涨停/跌停/连板指标生成情绪信号。"],
            error=None,
        )

    monkeypatch.setattr(v1_screening.service, "build_market_signal", fake_build_market_signal)
    response = client.post(
        "/api/v1/screen/market-signal",
        json={"trade_date": "2026-04-28", "use_demo_on_failure": True, "force_refresh": True},
        headers={"X-Client-Type": "web-desktop"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"]["degraded"] is True


def test_v1_board_top10_limit_up_response() -> None:
    response = client.post(
        "/api/v1/screen/board-top10-limit-up",
        json={"use_demo_on_failure": True},
        headers={"X-Client-Type": "windows-mfc"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"]["clientType"] == "windows-mfc"
    assert "items" in body["data"]


def test_v1_second_board_analysis_response() -> None:
    response = client.post(
        "/api/v1/screen/second-board-analysis",
        json={"trade_date": "2099-01-01", "use_demo_on_failure": True},
        headers={"X-Client-Type": "windows-mfc"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"]["clientType"] == "windows-mfc"
    assert "items" in body["data"]


def test_v1_second_board_analysis_future_date_no_backfill() -> None:
    response = client.post(
        "/api/v1/screen/second-board-analysis",
        json={"trade_date": "2099-01-01", "use_demo_on_failure": True, "force_refresh": True},
        headers={"X-Client-Type": "windows-mfc"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["trade_date"] == "2099-01-01"
    assert body["data"]["items"] == []
    assert any("尚未到达" in note for note in body["data"]["market_summary"]["notes"])
    assert any("不返回历史缓存回填" in note for note in body["data"]["market_summary"]["notes"])


def test_second_board_analysis_future_date_no_backfill() -> None:
    response = client.post(
        "/screen/second-board-analysis",
        json={"trade_date": "2099-01-01", "use_demo_on_failure": True, "force_refresh": True},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["trade_date"] == "2099-01-01"
    assert body["items"] == []
    assert any("尚未到达" in note for note in body["market_summary"]["notes"])
    assert any("不返回历史缓存回填" in note for note in body["market_summary"]["notes"])


def test_v1_market_signal_future_date_no_backfill() -> None:
    response = client.post(
        "/api/v1/screen/market-signal",
        json={"trade_date": "2099-01-01", "use_demo_on_failure": True, "force_refresh": True},
        headers={"X-Client-Type": "windows-mfc"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["trade_date"] == "2099-01-01"
    assert body["data"]["indicators"] == []
    assert "尚未到达" in body["data"]["marketOverview"]
    assert any("不返回历史缓存回填" in note for note in body["data"]["notes"])


def test_v1_market_signal_unclosed_day_no_backfill(monkeypatch) -> None:
    def fake_build_market_signal(
        trade_date: str | None,
        use_demo_on_failure: bool,
        force_refresh: bool = False,
    ) -> MarketSignalResponse:
        return MarketSignalResponse(
            trade_date=trade_date or "2026-04-21",
            weekday="周二",
            marketOverview="当日尚未收盘，暂无可用指数收盘数据。",
            turnoverOverview="当日尚未收盘，暂无可用沪深京成交额收盘数据。",
            regime="YELLOW",
            regimeLabel="黄灯",
            positionAdvice="当日未收盘，建议仅观察，不执行收盘后策略。",
            indicators=[],
            notes=["交易日未收盘，已停止使用昨日缓存/历史数据回填。"],
            error=None,
        )

    monkeypatch.setattr(v1_screening.service, "build_market_signal", fake_build_market_signal)
    response = client.post(
        "/api/v1/screen/market-signal",
        json={"trade_date": "2026-04-21", "use_demo_on_failure": True, "force_refresh": True},
        headers={"X-Client-Type": "android"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["trade_date"] == "2026-04-21"
    assert body["data"]["indicators"] == []
    assert "暂无可用指数收盘数据" in body["data"]["marketOverview"]
    assert any("停止使用昨日缓存" in note for note in body["data"]["notes"])


def test_v1_first_board_future_date_no_backfill() -> None:
    response = client.post(
        "/api/v1/screen/first-board",
        json={"trade_date": "2099-01-01", "use_demo_on_failure": True, "force_refresh": True},
        headers={"X-Client-Type": "windows-mfc"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["trade_date"] == "2099-01-01"
    assert body["data"]["items"] == []
    assert any("尚未到达" in note for note in body["data"]["market_summary"]["notes"])
    assert any("不返回历史缓存回填" in note for note in body["data"]["market_summary"]["notes"])


def test_v1_top5_future_date_no_backfill() -> None:
    response = client.post(
        "/api/v1/screen/top5",
        json={"trade_date": "2099-01-01", "use_demo_on_failure": True, "force_refresh": True},
        headers={"X-Client-Type": "windows-mfc"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["trade_date"] == "2099-01-01"
    assert body["data"]["items"] == []
    assert any("尚未到达" in note for note in body["data"]["market_summary"]["notes"])


class EmptyDataService:
    def get_market_dataset(self, trade_date: str | None = None, force_refresh: bool = False) -> MarketDataset:
        return MarketDataset(
            trade_date="2026-04-15",
            source="empty",
            limit_up_pool=pd.DataFrame(),
            previous_limit_up_pool=pd.DataFrame(),
            board_snapshot=pd.DataFrame(),
        )


def test_empty_dataset_uses_demo_when_enabled() -> None:
    service = ScreenerService(data_service=EmptyDataService())
    response = service.screen_first_board("20260415", use_demo_on_failure=True)
    assert response.market_summary.source == "demo"
    assert len(response.items) > 0


class HistoryUnavailableDataService:
    def get_market_dataset(self, trade_date: str | None = None, force_refresh: bool = False) -> MarketDataset:
        limit_up_pool = pd.DataFrame(
            [
                {
                    "名称": "实时首板A",
                    "代码": "002111",
                    "连板数": 1,
                    "流通市值": 86.4,
                    "换手率": 11.23,
                    "封板资金": 1.26,
                    "所属行业": "半导体",
                    "首次封板时间": "094712",
                    "最新价": 12.5,
                    "涨停原因类别": "半导体国产替代",
                }
            ]
        )
        return MarketDataset(
            trade_date="2026-04-15",
            source="live",
            limit_up_pool=limit_up_pool,
            previous_limit_up_pool=pd.DataFrame(),
            board_snapshot=pd.DataFrame(),
        )

    def get_stock_history(
        self,
        symbol: str,
        trade_date: str | None = None,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        raise ConnectionError("historical data unavailable")


def test_first_board_skips_history_filter_when_history_unavailable() -> None:
    service = ScreenerService(data_service=HistoryUnavailableDataService())
    response = service.screen_first_board("20260415", use_demo_on_failure=True)
    assert response.market_summary.source == "live"
    assert len(response.items) == 1
    assert any("历史行情不可用" in note for note in response.market_summary.notes)
    assert "历史日线不可用" not in response.items[0].recommendReason


class FirstBoardPriceOutOfRangeDataService:
    def get_market_dataset(self, trade_date: str | None = None, force_refresh: bool = False) -> MarketDataset:
        limit_up_pool = pd.DataFrame(
            [
                {
                    "名称": "低价首板",
                    "代码": "002222",
                    "连板数": 1,
                    "流通市值": 66.0,
                    "换手率": 10.5,
                    "封板资金": 1.88,
                    "所属行业": "电子",
                    "首次封板时间": "094512",
                    "最后封板时间": "094700",
                    "炸板次数": 0,
                    "最新价": 1.82,
                }
            ]
        )
        board_snapshot = pd.DataFrame([{"板块名称": "电子", "涨跌幅": 1.2}])
        return MarketDataset(
            trade_date="2026-04-15",
            source="live",
            limit_up_pool=limit_up_pool,
            previous_limit_up_pool=pd.DataFrame(),
            board_snapshot=board_snapshot,
        )

    def get_stock_history(
        self,
        symbol: str,
        trade_date: str | None = None,
        force_refresh: bool = False,
        allow_live_fetch: bool = True,
    ) -> pd.DataFrame:
        return pd.DataFrame()


def test_first_board_filters_price_outside_2_to_40() -> None:
    service = ScreenerService(data_service=FirstBoardPriceOutOfRangeDataService())
    response = service.screen_first_board("20260415", use_demo_on_failure=False)
    assert response.items == []


class WeakToStrongPriceOutOfRangeDataService:
    def get_market_dataset(self, trade_date: str | None = None, force_refresh: bool = False) -> MarketDataset:
        limit_up_pool = pd.DataFrame(
            [
                {
                    "名称": "高价弱转强",
                    "代码": "002333",
                    "连板数": 2,
                    "流通市值": 88.0,
                    "换手率": 9.0,
                    "封板资金": 2.36,
                    "所属行业": "机器人",
                    "首次封板时间": "142000",
                    "最后封板时间": "145600",
                    "炸板次数": 1,
                    "最新价": 45.3,
                    "涨跌幅": 10.01,
                }
            ]
        )
        board_snapshot = pd.DataFrame([{"板块名称": "机器人", "涨跌幅": 2.2}])
        return MarketDataset(
            trade_date="2026-04-15",
            source="live",
            limit_up_pool=limit_up_pool,
            previous_limit_up_pool=pd.DataFrame(),
            board_snapshot=board_snapshot,
        )


def test_weak_to_strong_filters_price_outside_2_to_40() -> None:
    service = ScreenerService(data_service=WeakToStrongPriceOutOfRangeDataService())
    response = service.screen_weak_to_strong("20260415", use_demo_on_failure=False)
    assert response.items == []


class BoardTop10ScoreCapDataService:
    def get_market_dataset(self, trade_date: str | None = None, force_refresh: bool = False) -> MarketDataset:
        limit_up_pool = pd.DataFrame(
            [
                {
                    "名称": "板块前10样本",
                    "代码": "002555",
                    "连板数": 2,
                    "流通市值": 120.0,
                    "换手率": 12.8,
                    "封板资金": 2.8,
                    "所属行业": "机器人",
                    "首次封板时间": "094201",
                    "最后封板时间": "094300",
                    "炸板次数": 0,
                    "最新价": 18.3,
                    "涨跌幅": 10.01,
                }
            ]
        )
        board_snapshot = pd.DataFrame([{"板块名称": "机器人", "涨跌幅": 3.2}])
        return MarketDataset(
            trade_date="2026-04-15",
            source="live",
            limit_up_pool=limit_up_pool,
            previous_limit_up_pool=pd.DataFrame(),
            board_snapshot=board_snapshot,
        )


def test_board_top10_limit_up_score_not_exceed_27() -> None:
    service = ScreenerService(data_service=BoardTop10ScoreCapDataService())
    response = service.screen_board_top10_limit_up("20260415", use_demo_on_failure=False)
    assert len(response.items) == 1
    assert response.items[0].totalScore is not None
    assert response.items[0].totalScore <= 27


class SecondBoardAnalysisDataService:
    def get_market_dataset(self, trade_date: str | None = None, force_refresh: bool = False) -> MarketDataset:
        limit_up_pool = pd.DataFrame(
            [
                {
                    "名称": "有效二板A",
                    "代码": "002001",
                    "连板数": 2,
                    "流通市值": 8_000_000_000,
                    "换手率": 8.0,
                    "封板资金": 120_000_000,
                    "所属行业": "机器人",
                    "首次封板时间": "093000",
                    "炸板次数": 0,
                    "最新价": 12.0,
                    "成交额": 200_000_000,
                },
                {
                    "名称": "有效二板B",
                    "代码": "603001",
                    "连板数": 2,
                    "流通市值": 9_000_000_000,
                    "换手率": 6.0,
                    "封板资金": 80_000_000,
                    "所属行业": "电力",
                    "首次封板时间": "094000",
                    "炸板次数": 1,
                    "最新价": 10.0,
                    "成交额": 80_000_000,
                },
                {
                    "名称": "有效二板C",
                    "代码": "002002",
                    "连板数": 2,
                    "流通市值": 9_000_000_000,
                    "换手率": 6.0,
                    "封板资金": 80_000_000,
                    "所属行业": "电力",
                    "首次封板时间": "094500",
                    "炸板次数": 1,
                    "最新价": 10.0,
                    "成交额": 100_000_000,
                },
                {
                    "名称": "创业二板",
                    "代码": "300001",
                    "连板数": 2,
                    "流通市值": 8_000_000_000,
                    "换手率": 8.0,
                    "封板资金": 120_000_000,
                    "所属行业": "机器人",
                    "首次封板时间": "093000",
                    "炸板次数": 0,
                    "最新价": 12.0,
                    "成交额": 200_000_000,
                },
                {
                    "名称": "ST样本",
                    "代码": "002003",
                    "连板数": 2,
                    "流通市值": 8_000_000_000,
                    "换手率": 8.0,
                    "封板资金": 120_000_000,
                    "所属行业": "机器人",
                    "首次封板时间": "093000",
                    "炸板次数": 0,
                    "最新价": 12.0,
                    "成交额": 200_000_000,
                },
            ]
        )
        return MarketDataset(
            trade_date="2026-04-15",
            source="live",
            limit_up_pool=limit_up_pool,
            previous_limit_up_pool=pd.DataFrame(),
            board_snapshot=pd.DataFrame(),
        )

    def get_stock_history(
        self,
        symbol: str,
        trade_date: str | None = None,
        force_refresh: bool = False,
        allow_live_fetch: bool = False,
    ) -> pd.DataFrame:
        if symbol == "603001":
            amounts = [100_000_000, 100_000_000, 100_000_000, 100_000_000, 100_000_000]
        elif symbol == "002002":
            return pd.DataFrame()
        else:
            amounts = [100_000_000, 100_000_000, 100_000_000, 100_000_000, 100_000_000]
        return pd.DataFrame(
            {
                "日期": ["2026-04-08", "2026-04-09", "2026-04-10", "2026-04-11", "2026-04-14"],
                "成交额": amounts,
            }
        )


def test_second_board_analysis_filters_sorts_and_calculates_energy() -> None:
    service = ScreenerService(data_service=SecondBoardAnalysisDataService())
    response = service.screen_second_board_analysis("20260415", use_demo_on_failure=False)
    assert response.market_summary.secondBoardCount == 3
    assert [item.symbol for item in response.items] == ["002001", "603001", "002002"]
    assert response.items[0].firstBoardEnergy == "2.00"
    assert response.items[1].firstBoardEnergy == "0"
    assert response.items[2].firstBoardEnergy == "W"
    assert all(not item.symbol.startswith("300") for item in response.items)
    assert all("ST" not in item.stockName for item in response.items)


class MarketSignalNoCloseDataService:
    def get_market_dataset(self, trade_date: str | None = None, force_refresh: bool = False) -> MarketDataset:
        return MarketDataset(
            trade_date="2026-04-21",
            source="cache",
            limit_up_pool=pd.DataFrame(),
            previous_limit_up_pool=pd.DataFrame(),
            board_snapshot=pd.DataFrame(),
        )

    def get_limit_down_pool(self, trade_date: str | None = None, force_refresh: bool = False) -> pd.DataFrame:
        return pd.DataFrame()

    def get_market_overview(
        self,
        trade_date: str | None = None,
        force_refresh: bool = False,
    ) -> MarketOverviewSnapshot:
        return MarketOverviewSnapshot(
            market_overview="当日尚未收盘，暂无可用指数收盘数据。",
            turnover_overview="当日尚未收盘，暂无可用沪深京成交额收盘数据。",
            notes=["交易日未收盘，已停止使用昨日缓存/历史数据回填。"],
            has_valid_close=False,
        )


def test_market_signal_future_date_returns_no_backfill_message() -> None:
    service = ScreenerService(data_service=MarketSignalNoCloseDataService())
    response = service.build_market_signal("2099-01-01", use_demo_on_failure=True)
    assert response.trade_date == "2099-01-01"
    assert response.indicators == []
    assert "尚未到达" in response.marketOverview
    assert any("不返回历史缓存回填" in note for note in response.notes)


def test_market_signal_no_close_returns_empty_indicators() -> None:
    service = ScreenerService(data_service=MarketSignalNoCloseDataService())
    response = service.build_market_signal("2026-04-21", use_demo_on_failure=True)
    assert response.indicators == []
    assert "暂无可用指数收盘数据" in response.marketOverview
    assert "暂无可用沪深京成交额收盘数据" in response.turnoverOverview


def test_extract_index_snapshot_requires_exact_trade_date() -> None:
    index_frame = pd.DataFrame(
        [
            {"date": datetime(2026, 4, 17), "close": 3200.0, "amount": 400_000_000_000},
            {"date": datetime(2026, 4, 18), "close": 3250.0, "amount": 420_000_000_000},
        ]
    )
    # Asking for 2026-04-19 must not fallback to 2026-04-18.
    snapshot = AkshareDataService._extract_index_snapshot(index_frame, "2026-04-19", "沪指")
    assert snapshot is None
