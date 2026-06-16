# Android Zero-Regression Checklist

本清单用于验证第一阶段基础改造没有破坏现有 Android 主线功能。

## Backend Reachability

- `GET /health` 返回 `{"status":"ok"}`
- 旧路径 `/screen/*` 仍可访问
- `/api/v1/*` 新路径新增后不影响旧路径响应

## Android Home Flow

- 首页仍显示：
  - `情绪信号`
  - `一进二选股`
  - `弱转强选股`
  - `Top5 推荐`
- 首页仍可编辑后端地址和交易日
- 点击按钮后仍会先进入目标页并展示 loading

## Legacy Endpoint Contracts

- `POST /screen/market-signal` 返回旧结构
- `POST /screen/first-board` 返回旧结构
- `POST /screen/weak-to-strong` 返回旧结构
- `POST /screen/top5` 返回旧结构

## Cache Behavior

- 同按钮 2 小时内优先命中 Android 本地缓存
- 结果页点击“刷新”会强制请求最新数据
- 网络失败时若缓存仍有效，会继续展示缓存结果

## User Visible Result Pages

- 情绪信号页可正常展示摘要、指标和备注
- 一进二页可正常展示摘要卡与候选列表
- 弱转强页可正常展示候选列表
- Top5 页可正常展示推荐列表
- 返回与刷新按钮行为正常

## Failure Modes

- 后端异常时 Android 仍能显示错误提示
- 服务降级到缓存或 demo 时不崩溃
