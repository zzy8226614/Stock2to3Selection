# Stock2to3Selection

二进三选股系统，包含 FastAPI 后端、Android 客户端、Web/Windows 客户端工程骨架和项目文档。

## 核心功能

- 情绪信号：涨停情绪、连板高度、大盘表现、成交额概览。
- 二板解析：筛选二进三候选标的，计算首板量能、题材、封单等字段。
- 板块个股排名：按板块汇总并返回涨停个股排名。
- 上游容错：Akshare 不稳定时使用本地缓存和腾讯行情后备源兜底。

## 后端本地运行

PowerShell 默认安全策略可能禁止直接执行脚本。推荐使用一次性绕过方式：

```powershell
powershell -ExecutionPolicy Bypass -File .\backend\run_server.ps1
```

也可以手动启动：

```powershell
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8081
```

健康检查：

```text
http://127.0.0.1:8081/health
http://127.0.0.1:8081/api/v1/health
```

## 核心接口

API v1:

- `POST /api/v1/screen/market-signal`
- `POST /api/v1/screen/second-board-analysis`
- `POST /api/v1/screen/board-top10-limit-up`

Legacy 兼容接口：

- `POST /screen/market-signal`
- `POST /screen/second-board-analysis`
- `POST /screen/board-top10-limit-up`

上游诊断：

- `GET /debug/upstream-check?timeout_seconds=12`

## 服务端缓存

后端缓存位于 `backend/app/data/cache/`，默认自动保留最近 30 天。可通过环境变量调整：

```bash
STOCK_CACHE_RETENTION_DAYS=30
```

设置为 `0` 可关闭自动清理。

## 测试

```powershell
python -m pytest backend\tests
```

## Android 构建

Release 构建命令示例：

```powershell
cd android-app
$env:JAVA_HOME="C:\Users\zhuzy\.jdks\jbr-17.0.14"
$env:PATH="$env:JAVA_HOME\bin;$env:PATH"
$env:GRADLE_USER_HOME="C:\Users\zhuzy\.gradle"
& "C:\Users\zhuzy\.gradle\wrapper\dists\gradle-8.14-all\c2qonpi39x1mddn7hk5gh9iqj\gradle-8.14\bin\gradle.bat" assembleRelease -x lintVitalRelease --no-daemon
```

签名文件不提交到 Git 仓库。若需要正式签名包，在本地保留：

- `android-app/release-signing.properties`
- `android-app/signing/*.jks`

没有签名配置时，当前 Gradle 脚本会用 debug signingConfig 兜底生成可安装包。

## 部署

阿里云部署步骤见 [docs/deployment/aliyun-backend-deployment.md](docs/deployment/aliyun-backend-deployment.md)。

GitHub 仓库：

```text
https://github.com/zzy8226614/Stock2to3Selection.git
```
