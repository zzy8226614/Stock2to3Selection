# Windows Host Run Guide

## Prerequisites

- Windows 10
- 若走 `WebView2 + MFC` 路线：Visual Studio 2022 with MFC support、CMake 3.25+、WebView2 SDK
- 若走 `WinForms` 路线：当前机器自带的 .NET Framework 编译器即可

## Recommended On This Machine

当前机器缺少现代 MFC/WebView2 编译环境，但可以直接产出 `WinForms` 宿主 exe。

### 直接构建 exe

```powershell
.\windows-mfc\build-winforms.bat
```

产物：

```text
windows-mfc\build-winforms\MoneyAppDesktop.exe
```

### 运行前准备

1. 启动本机后端
2. 确认 `http://127.0.0.1:8000/desktop-shell/` 可访问
3. 运行 `windows-mfc\build-winforms\MoneyAppDesktop.exe`

## Environment

设置 WebView2 SDK 路径：

```powershell
$env:WEBVIEW2_SDK_PATH="C:\path\to\Microsoft.Web.WebView2.<version>"
```

## Build

在仓库根目录执行：

```powershell
cmake -S windows-mfc -B windows-mfc/build -A x64
cmake --build windows-mfc/build --config Debug
```

## Run

1. 确保本机后端已启动
2. 启动生成的 `MoneyAppDesktop.exe`
3. 宿主会自动加载 `web/desktop-shell/index.html`
4. 在桌面壳层中保存后端地址后，可直接调用 `/api/v1/screen/*`

## Current Phase Limit

- 当前 WinForms 宿主已经可以作为 Win10 可运行 exe 打开桌面壳层
- 当前宿主已经具备 WebView2 加载、配置同步和消息桥基础能力
- 还未实现完整盘前计划/盘中监控/盘后复盘桌面功能
- 当前机器上的原生 MFC 编译仍受缺失的 Windows SDK 桌面库限制
