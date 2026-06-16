# Legacy API Contract

本文件冻结当前 Android 客户端已经依赖的旧接口契约。以下路径、字段和行为在旧客户端退役前视为稳定基线，不做破坏性修改。

## Stable Endpoints

- `GET /health`
- `POST /screen/market-signal`
- `POST /screen/first-board`
- `POST /screen/weak-to-strong`
- `POST /screen/top5`

## Stable Request Shape

所有旧版选股接口均接收同一请求体：

```json
{
  "trade_date": "2026-04-17",
  "use_demo_on_failure": false,
  "force_refresh": false
}
```

说明：

- `trade_date` 允许 `YYYY-MM-DD` 或 `YYYYMMDD`，为空则按当天处理。
- `use_demo_on_failure` 是服务端降级开关。
- `force_refresh` 会绕过客户端与服务端的缓存优先策略。

## Stable Response Shape

旧接口继续返回 Android 已绑定的响应结构，不增加必须字段，不变更既有 key 命名。

### `POST /screen/market-signal`

- 顶层保持：
  - `trade_date`
  - `weekday`
  - `marketOverview`
  - `turnoverOverview`
  - `regime`
  - `regimeLabel`
  - `positionAdvice`
  - `indicators`
  - `notes`
  - `error`

### `POST /screen/first-board` / `weak-to-strong` / `top5`

- 顶层保持：
  - `trade_date`
  - `market_summary`
  - `items`
  - `error`

- `market_summary` 保持：
  - `tradeDate`
  - `limitUpCount`
  - `firstBoardCount`
  - `weakToStrongCount`
  - `source`
  - `notes`

- `items` 中字段保持 Android 当前模型命名：
  - `stockName`
  - `symbol`
  - `floatMarketCap`
  - `boardName`
  - `boardRank`
  - `boardLimitUpCount`
  - `turnoverRate`
  - `sealTime`
  - `sealOrderLots`
  - `openBoardCount`
  - `totalScore`
  - `isLimitUp`
  - `strategyTag`
  - `recommendReason`

## Legacy Error Semantics

- 旧接口继续沿用当前行为：
  - 服务成功时：`HTTP 200`
  - 服务内部异常时：`HTTP 500`，返回 FastAPI 默认错误体，例如：

```json
{
  "detail": "Failed to build market signal: ..."
}
```

- 旧接口不会引入新的统一错误 envelope，以避免破坏 Android 客户端的现有解析逻辑。

## Android Cache Contract

以下行为由 Android 客户端实现，视为旧版兼容契约的一部分：

- 缓存键：`screenType + baseUrl + tradeDate`
- 成功结果缓存 TTL：`2` 小时
- 同按钮再次进入优先展示缓存
- 手动点击“刷新”时强制走 `force_refresh=true`
- 若网络失败但缓存仍有效，则优先展示缓存结果

对应实现基线：

- `android-app/app/src/main/java/com/moneyapp/screener/repository/ScreeningRepository.kt`
- `android-app/app/src/main/java/com/moneyapp/screener/repository/LocalResultCache.kt`
- `android-app/app/src/main/java/com/moneyapp/screener/ui/ScreeningViewModel.kt`

## Compatibility Rules

- 旧接口只允许新增“可忽略”的非必填字段，禁止删除或重命名既有字段。
- 旧接口若需要破坏性调整，必须迁移到 `/api/v1` 之后的新版本路径。
- Android 客户端默认继续使用旧路径，直到显式迁移完成。
