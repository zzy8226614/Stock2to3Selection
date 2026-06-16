from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .schemas import MarketSignalResponse, ScreeningRequest, ScreeningResponse

ClientType = Literal["android", "windows-mfc", "web-desktop", "unknown"]
ResponseSource = Literal["live", "cache", "demo", "mixed", "unknown"]


class ClientContext(BaseModel):
    client_type: ClientType = "unknown"
    request_id: str


class ApiV1Request(ScreeningRequest):
    pass


class ApiV1Meta(BaseModel):
    requestId: str
    clientType: ClientType
    cacheHit: bool = False
    degraded: bool = False
    source: ResponseSource = "unknown"
    upstreamSource: str | None = None


class ApiV1Error(BaseModel):
    code: str
    message: str
    detail: str | None = None
    requestId: str
    clientType: ClientType


class ApiV1HealthResponse(BaseModel):
    success: bool = True
    data: dict[str, str]
    meta: ApiV1Meta
    error: ApiV1Error | None = None


class ApiV1ScreeningEnvelope(BaseModel):
    success: bool = True
    data: ScreeningResponse
    meta: ApiV1Meta
    error: ApiV1Error | None = None


class ApiV1MarketSignalEnvelope(BaseModel):
    success: bool = True
    data: MarketSignalResponse
    meta: ApiV1Meta
    error: ApiV1Error | None = None


class ApiV1ErrorEnvelope(BaseModel):
    success: bool = False
    data: dict[str, str] = Field(default_factory=dict)
    meta: ApiV1Meta
    error: ApiV1Error
