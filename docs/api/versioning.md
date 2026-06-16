# API Versioning Policy

## Why

仓库现在同时服务 Android 客户端和未来的 Windows 10 MFC + WebView2 客户端。为了在不打断 Android 现网功能的前提下继续演进，接口采用“双轨制”：

- 旧路径：兼容 Android 的 legacy contract
- 新路径：`/api/v1/*`，用于多端统一治理

## Routing Strategy

### Legacy

- `GET /health`
- `POST /screen/market-signal`
- `POST /screen/first-board`
- `POST /screen/weak-to-strong`
- `POST /screen/top5`

### Versioned

- `GET /api/v1/health`
- `POST /api/v1/screen/market-signal`
- `POST /api/v1/screen/first-board`
- `POST /api/v1/screen/weak-to-strong`
- `POST /api/v1/screen/top5`

## v1 Envelope

`/api/v1/*` 统一返回 envelope 结构：

```json
{
  "success": true,
  "data": {},
  "meta": {
    "requestId": "uuid",
    "clientType": "windows-mfc",
    "cacheHit": false,
    "degraded": false,
    "source": "live",
    "upstreamSource": "live"
  },
  "error": null
}
```

失败时：

```json
{
  "success": false,
  "data": {},
  "meta": {
    "requestId": "uuid",
    "clientType": "windows-mfc",
    "cacheHit": false,
    "degraded": false,
    "source": "unknown",
    "upstreamSource": null
  },
  "error": {
    "code": "SCREENING_UPSTREAM_FAILED",
    "message": "Failed to load screening data.",
    "detail": "具体异常",
    "requestId": "uuid",
    "clientType": "windows-mfc"
  }
}
```

## Client Identification

`/api/v1/*` 建议客户端通过 `X-Client-Type` 传递调用来源：

- `android`
- `windows-mfc`
- `web-desktop`

未知值会被归一化为 `unknown`。

## Change Rules

- Legacy 路径只修 bug，不做破坏性字段调整。
- 新字段优先加在 `/api/v1/*` 的 `meta` 中。
- 若 `data` 结构需要破坏性调整，新增 `/api/v2/*`，不在 `/api/v1/*` 内直接变更。
- 任何破坏性变更必须同步更新：
  - `docs/api/versioning.md`
  - `docs/api/legacy-contract.md`
  - `Spec.md`

## Migration Plan

1. Android 继续维持旧路径。
2. Windows 客户端首版优先接入 `/api/v1/*`。
3. 当 Android 完成升级并验证通过后，再决定是否收敛旧路径。
