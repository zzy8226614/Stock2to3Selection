from __future__ import annotations

from typing import Callable
from uuid import uuid4
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Header, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..models.api_v1 import (
    ApiV1Error,
    ApiV1ErrorEnvelope,
    ApiV1HealthResponse,
    ApiV1MarketSignalEnvelope,
    ApiV1Meta,
    ApiV1Request,
    ApiV1ScreeningEnvelope,
    ClientContext,
    ClientType,
    ResponseSource,
)
from ..models.schemas import MarketSignalResponse, ScreeningResponse
from ..services.cache_service import JsonCacheService
from ..services.screener_service import ScreenerService

router = APIRouter(prefix="/api/v1", tags=["screening-v1"])
service = ScreenerService()
response_cache = JsonCacheService()
CN_TZ = ZoneInfo("Asia/Shanghai")

CLIENT_ALIASES: dict[str, ClientType] = {
    "android": "android",
    "windows-mfc": "windows-mfc",
    "mfc": "windows-mfc",
    "desktop": "windows-mfc",
    "web-desktop": "web-desktop",
    "web": "web-desktop",
}


def _request_context(request: Request, client_type_header: str | None) -> ClientContext:
    raw_request_id = request.headers.get("X-Request-Id") or str(uuid4())
    normalized_client_type = CLIENT_ALIASES.get((client_type_header or "").strip().lower(), "unknown")
    return ClientContext(client_type=normalized_client_type, request_id=raw_request_id)


def _response_source_from_text(source_text: str | None) -> ResponseSource:
    normalized = (source_text or "").strip().lower()
    if not normalized:
        return "unknown"
    if normalized == "demo":
        return "demo"
    if "cache" in normalized and "live" in normalized:
        return "mixed"
    if "cache" in normalized:
        return "cache"
    if "live" in normalized:
        return "live"
    return "unknown"


def _normalized_trade_date_key(trade_date: str | None) -> str:
    if not trade_date:
        return datetime.now(CN_TZ).strftime("%Y%m%d")
    return trade_date.replace("-", "")


def _market_signal_meta(response: MarketSignalResponse, context: ClientContext) -> ApiV1Meta:
    notes_blob = " ".join(response.notes).lower()
    has_cache_hint = ("缓存" in notes_blob) or ("cache" in notes_blob)
    has_demo_hint = ("fallback" in notes_blob) or ("demo" in notes_blob)
    has_degraded_hint = any(
        token in notes_blob
        for token in ("不可用", "失败", "降级", "仅基于", "暂不可用")
    ) or ("暂不可用" in response.marketOverview) or ("暂不可用" in response.turnoverOverview)

    if has_cache_hint and has_degraded_hint:
        source: ResponseSource = "mixed"
    elif has_cache_hint:
        source = "cache"
    elif has_demo_hint:
        source = "demo"
    else:
        source = "live" if not has_degraded_hint else "unknown"

    return ApiV1Meta(
        requestId=context.request_id,
        clientType=context.client_type,
        cacheHit=source in {"cache", "mixed"},
        degraded=has_degraded_hint or source in {"demo", "mixed"},
        source=source,
        upstreamSource=None,
    )


def _screening_meta(response: ScreeningResponse, context: ClientContext) -> ApiV1Meta:
    upstream_source = response.market_summary.source
    source = _response_source_from_text(upstream_source)
    return ApiV1Meta(
        requestId=context.request_id,
        clientType=context.client_type,
        cacheHit=source in {"cache", "mixed"},
        degraded=source in {"cache", "demo", "mixed"},
        source=source,
        upstreamSource=upstream_source,
    )


def _error_response(
    *,
    code: str,
    message: str,
    detail: str,
    context: ClientContext,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> JSONResponse:
    meta = ApiV1Meta(
        requestId=context.request_id,
        clientType=context.client_type,
        cacheHit=False,
        degraded=False,
        source="unknown",
        upstreamSource=None,
    )
    error = ApiV1Error(
        code=code,
        message=message,
        detail=detail,
        requestId=context.request_id,
        clientType=context.client_type,
    )
    return JSONResponse(
        status_code=status_code,
        content=ApiV1ErrorEnvelope(meta=meta, error=error).model_dump(),
        headers={"X-Request-Id": context.request_id},
    )


def _execute_screening(
    *,
    request: ApiV1Request,
    client_context: ClientContext,
    cache_key_prefix: str,
    response_factory: Callable[[ScreeningResponse, ApiV1Meta], ApiV1ScreeningEnvelope],
    block: Callable[[], ScreeningResponse],
) -> ApiV1ScreeningEnvelope | JSONResponse:
    cache_key = f"{cache_key_prefix}_{_normalized_trade_date_key(request.trade_date)}"
    if not request.force_refresh:
        cached_payload = response_cache.load(cache_key)
        if cached_payload is not None:
            cached_data = ScreeningResponse.model_validate(cached_payload)
            if not _is_stale_second_board_energy_cache(cache_key_prefix, cached_data):
                cached_meta = _screening_meta(cached_data, client_context).model_copy(
                    update={"cacheHit": True, "source": "cache", "degraded": True}
                )
                return response_factory(cached_data, cached_meta)

    try:
        result = block()
    except Exception as exc:
        return _error_response(
            code="SCREENING_UPSTREAM_FAILED",
            message="Failed to load screening data.",
            detail=str(exc),
            context=client_context,
        )
    # Always refresh cache with latest successful payload so force_refresh
    # can heal stale same-day cached responses for later normal requests.
    if not _is_stale_second_board_energy_cache(cache_key_prefix, result):
        response_cache.save(cache_key, result.model_dump())
    meta = _screening_meta(result, client_context)
    return response_factory(result, meta)


def _is_stale_second_board_energy_cache(cache_key_prefix: str, response: ScreeningResponse) -> bool:
    if cache_key_prefix != "resp_second_board_analysis":
        return False
    if not response.items:
        return False
    return all(item.firstBoardEnergy == "W" for item in response.items)


@router.get("/health", response_model=ApiV1HealthResponse)
def health_v1(
    request: Request,
    response: Response,
    x_client_type: str | None = Header(default=None),
) -> ApiV1HealthResponse:
    context = _request_context(request, x_client_type)
    response.headers["X-Request-Id"] = context.request_id
    return ApiV1HealthResponse(
        data={"status": "ok"},
        meta=ApiV1Meta(
            requestId=context.request_id,
            clientType=context.client_type,
            cacheHit=False,
            degraded=False,
            source="live",
            upstreamSource="health",
        ),
    )


@router.post("/screen/first-board", response_model=ApiV1ScreeningEnvelope, responses={500: {"model": ApiV1ErrorEnvelope}})
def screen_first_board_v1(
    payload: ApiV1Request,
    request: Request,
    response: Response,
    x_client_type: str | None = Header(default=None),
) -> ApiV1ScreeningEnvelope | JSONResponse:
    context = _request_context(request, x_client_type)
    response.headers["X-Request-Id"] = context.request_id
    return _execute_screening(
        request=payload,
        client_context=context,
        cache_key_prefix="resp_first_board",
        response_factory=lambda data, meta: ApiV1ScreeningEnvelope(data=data, meta=meta),
        block=lambda: service.screen_first_board(
            trade_date=payload.trade_date,
            use_demo_on_failure=payload.use_demo_on_failure,
            force_refresh=payload.force_refresh,
        ),
    )


@router.post("/screen/weak-to-strong", response_model=ApiV1ScreeningEnvelope, responses={500: {"model": ApiV1ErrorEnvelope}})
def screen_weak_to_strong_v1(
    payload: ApiV1Request,
    request: Request,
    response: Response,
    x_client_type: str | None = Header(default=None),
) -> ApiV1ScreeningEnvelope | JSONResponse:
    context = _request_context(request, x_client_type)
    response.headers["X-Request-Id"] = context.request_id
    return _execute_screening(
        request=payload,
        client_context=context,
        cache_key_prefix="resp_weak_to_strong",
        response_factory=lambda data, meta: ApiV1ScreeningEnvelope(data=data, meta=meta),
        block=lambda: service.screen_weak_to_strong(
            trade_date=payload.trade_date,
            use_demo_on_failure=payload.use_demo_on_failure,
            force_refresh=payload.force_refresh,
        ),
    )


@router.post("/screen/top5", response_model=ApiV1ScreeningEnvelope, responses={500: {"model": ApiV1ErrorEnvelope}})
def screen_top5_v1(
    payload: ApiV1Request,
    request: Request,
    response: Response,
    x_client_type: str | None = Header(default=None),
) -> ApiV1ScreeningEnvelope | JSONResponse:
    context = _request_context(request, x_client_type)
    response.headers["X-Request-Id"] = context.request_id
    return _execute_screening(
        request=payload,
        client_context=context,
        cache_key_prefix="resp_top5",
        response_factory=lambda data, meta: ApiV1ScreeningEnvelope(data=data, meta=meta),
        block=lambda: service.screen_top5(
            trade_date=payload.trade_date,
            use_demo_on_failure=payload.use_demo_on_failure,
            force_refresh=payload.force_refresh,
        ),
    )


@router.post(
    "/screen/board-top10-limit-up",
    response_model=ApiV1ScreeningEnvelope,
    responses={500: {"model": ApiV1ErrorEnvelope}},
)
def screen_board_top10_limit_up_v1(
    payload: ApiV1Request,
    request: Request,
    response: Response,
    x_client_type: str | None = Header(default=None),
) -> ApiV1ScreeningEnvelope | JSONResponse:
    context = _request_context(request, x_client_type)
    response.headers["X-Request-Id"] = context.request_id
    return _execute_screening(
        request=payload,
        client_context=context,
        cache_key_prefix="resp_board_top10_limit_up",
        response_factory=lambda data, meta: ApiV1ScreeningEnvelope(data=data, meta=meta),
        block=lambda: service.screen_board_top10_limit_up(
            trade_date=payload.trade_date,
            use_demo_on_failure=payload.use_demo_on_failure,
            force_refresh=payload.force_refresh,
        ),
    )


@router.post(
    "/screen/second-board-analysis",
    response_model=ApiV1ScreeningEnvelope,
    responses={500: {"model": ApiV1ErrorEnvelope}},
)
def screen_second_board_analysis_v1(
    payload: ApiV1Request,
    request: Request,
    response: Response,
    x_client_type: str | None = Header(default=None),
) -> ApiV1ScreeningEnvelope | JSONResponse:
    context = _request_context(request, x_client_type)
    response.headers["X-Request-Id"] = context.request_id
    return _execute_screening(
        request=payload,
        client_context=context,
        cache_key_prefix="resp_second_board_analysis",
        response_factory=lambda data, meta: ApiV1ScreeningEnvelope(data=data, meta=meta),
        block=lambda: service.screen_second_board_analysis(
            trade_date=payload.trade_date,
            use_demo_on_failure=payload.use_demo_on_failure,
            force_refresh=payload.force_refresh,
        ),
    )


@router.post("/screen/market-signal", response_model=ApiV1MarketSignalEnvelope, responses={500: {"model": ApiV1ErrorEnvelope}})
def market_signal_v1(
    payload: ApiV1Request,
    request: Request,
    response: Response,
    x_client_type: str | None = Header(default=None),
) -> ApiV1MarketSignalEnvelope | JSONResponse:
    context = _request_context(request, x_client_type)
    response.headers["X-Request-Id"] = context.request_id
    cache_key = f"resp_market_signal_{_normalized_trade_date_key(payload.trade_date)}"
    if not payload.force_refresh:
        cached_payload = response_cache.load(cache_key)
        if cached_payload is not None:
            cached_data = MarketSignalResponse.model_validate(cached_payload)
            cached_meta = _market_signal_meta(cached_data, context).model_copy(
                update={"cacheHit": True, "source": "cache"}
            )
            return ApiV1MarketSignalEnvelope(
                data=cached_data,
                meta=cached_meta,
            )
    try:
        result = service.build_market_signal(
            trade_date=payload.trade_date,
            use_demo_on_failure=payload.use_demo_on_failure,
            force_refresh=payload.force_refresh,
        )
    except Exception as exc:
        return _error_response(
            code="MARKET_SIGNAL_UPSTREAM_FAILED",
            message="Failed to load market signal data.",
            detail=str(exc),
            context=context,
        )
    # Always refresh cache with latest successful payload so force_refresh
    # can heal stale same-day cached responses for later normal requests.
    response_cache.save(cache_key, result.model_dump())
    return ApiV1MarketSignalEnvelope(
        data=result,
        meta=_market_signal_meta(result, context),
    )
