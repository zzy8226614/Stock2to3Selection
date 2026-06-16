# Windows Desktop Shell Architecture

## Goal

使用 `MFC + WebView2` 组合，先搭建 Windows 10 桌面端宿主基础设施，后续逐步扩展为盘前/盘中/盘后工具。

## Directory Split

- `windows-mfc/`: 原生宿主，负责窗口、菜单、配置、日志、WebView2 生命周期
- `web/desktop-shell/`: 被 WebView2 加载的桌面前端壳层

## Host Responsibilities

- 管理 WebView2 初始化
- 提供菜单、窗口、退出、设置面板
- 提供宿主级日志和请求诊断
- 管理本机配置与可选缓存目录
- 通过消息桥把宿主能力暴露给前端壳层

## Web Shell Responsibilities

- 呈现桌面端导航与页面壳层
- 调用 `/api/v1/*`
- 接收宿主下发的配置、日志、环境状态
- 展示请求耗时、缓存标记、错误 envelope

## Bridge Messages

### Host -> Web

```json
{
  "type": "host.config.sync",
  "payload": {
    "baseUrl": "http://127.0.0.1:8000/",
    "clientType": "windows-mfc"
  }
}
```

### Web -> Host

```json
{
  "type": "web.request.log",
  "payload": {
    "path": "/api/v1/screen/first-board",
    "method": "POST",
    "startedAt": "2026-04-17T12:00:00Z"
  }
}
```

## Phase 1 Intent

第一阶段只提供工程骨架和桥接协议，不在宿主中实现完整策略界面或本地数据库。

## Phase 3 Additions

当前桌面壳层已经补充以下基础交互：

- 首页与结果页双视图切换，流程贴近 Android 客户端
- 请求诊断面板，展示最近耗时、缓存命中、数据来源、降级状态
- 请求历史与宿主日志面板
- 宿主收到前端请求日志后回发 `host.request.received`
