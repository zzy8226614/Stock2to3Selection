from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ScreeningRequest(BaseModel):
    trade_date: str | None = Field(
        default=None,
        description="Trade date in YYYY-MM-DD or YYYYMMDD format. Defaults to today.",
    )
    use_demo_on_failure: bool = Field(
        default=True,
        description="Fallback to bundled demo data when Akshare is unavailable.",
    )
    force_refresh: bool = Field(
        default=False,
        description="Force refresh from live source and bypass client-side cache when supported.",
    )


class ScreeningItem(BaseModel):
    stockName: str
    symbol: str
    latestPrice: str = "--"
    floatMarketCap: str
    boardName: str
    boardRank: int = 0
    boardLimitUpCount: int
    ladderLevel: str = "--"
    turnoverRate: str
    sealTime: str
    sealOrderLots: str = "--"
    openBoardCount: int = 0
    totalScore: float | None = None
    firstBoardEnergy: str = "--"
    isLimitUp: bool = True
    strategyTag: Literal[
        "first_board_to_second",
        "weak_to_strong_2nd",
        "board_top10_limit_up",
        "second_board_analysis",
    ]
    recommendReason: str


class MarketSummary(BaseModel):
    tradeDate: str
    limitUpCount: int
    firstBoardCount: int
    weakToStrongCount: int
    secondBoardCount: int = 0
    source: str
    notes: list[str] = Field(default_factory=list)


class ScreeningResponse(BaseModel):
    trade_date: str
    market_summary: MarketSummary
    items: list[ScreeningItem] = Field(default_factory=list)
    error: str | None = None


class MarketSignalIndicator(BaseModel):
    name: str
    todayValue: str
    standard: str
    status: str


class MarketSignalResponse(BaseModel):
    trade_date: str
    weekday: str
    marketOverview: str
    turnoverOverview: str
    regime: Literal["GREEN", "YELLOW", "RED"]
    regimeLabel: str
    positionAdvice: str
    indicators: list[MarketSignalIndicator] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    error: str | None = None


class ApiError(BaseModel):
    detail: str
