#include "MainFrame.h"

#include <filesystem>

#ifndef MONEYAPP_REPO_ROOT
#define MONEYAPP_REPO_ROOT L"."
#endif

namespace moneyapp {

BEGIN_MESSAGE_MAP(MainFrame, CFrameWnd)
    ON_WM_CREATE()
    ON_WM_SIZE()
    ON_WM_CLOSE()
END_MESSAGE_MAP()

MainFrame::MainFrame() {
    config_ = config_store_.Load();
}

int MainFrame::OnCreate(LPCREATESTRUCT lpCreateStruct) {
    if (CFrameWnd::OnCreate(lpCreateStruct) == -1) {
        return -1;
    }

    CRect clientRect;
    GetClientRect(&clientRect);
    if (!browser_container_.Create(
            AfxRegisterWndClass(0),
            L"MoneyAPPBrowserContainer",
            WS_CHILD | WS_VISIBLE | WS_CLIPCHILDREN | WS_CLIPSIBLINGS,
            clientRect,
            this,
            1001
        )) {
        return -1;
    }

    webview_host_.SetMessageCallback([this](const std::wstring& rawJson) {
        HandleWebMessage(rawJson);
    });
    webview_host_.SetReadyCallback([this]() {
        SyncConfigToWeb();
    });
    webview_host_.SetStatusCallback([this](const std::wstring& message) {
        PostStatus(L"info", message);
    });

    if (!webview_host_.Initialize(browser_container_.GetSafeHwnd(), ResolveDesktopShellUrl())) {
        PostStatus(L"error", L"WebView2 initialization did not start.");
    }
    return 0;
}

void MainFrame::OnSize(UINT type, int cx, int cy) {
    CFrameWnd::OnSize(type, cx, cy);
    if (browser_container_.GetSafeHwnd()) {
        browser_container_.MoveWindow(0, 0, cx, cy);
        webview_host_.Resize();
    }
}

void MainFrame::OnClose() {
    webview_host_.SendJson(bridge_.BuildStatusMessage({L"info", L"Host window is closing."}));
    CFrameWnd::OnClose();
}

void MainFrame::SyncConfigToWeb() {
    webview_host_.SendJson(bridge_.BuildConfigSyncMessage(config_));
}

void MainFrame::HandleWebMessage(const std::wstring& rawJson) {
    const auto parsed = bridge_.ParseIncomingMessage(rawJson);
    if (!parsed.has_value()) {
        PostStatus(L"warn", L"Received malformed message from web shell.");
        return;
    }

    switch (parsed->kind) {
    case IncomingMessageKind::RequestLog:
        webview_host_.SendJson(bridge_.BuildRequestReceiptMessage(parsed->requestLog));
        PostStatus(
            L"request",
            L"Queued " + parsed->requestLog.method + L" " + parsed->requestLog.path + L" @ " + parsed->requestLog.baseUrl
        );
        break;
    case IncomingMessageKind::ConfigSave:
        config_ = parsed->config;
        if (config_store_.Save(config_)) {
            PostStatus(L"info", L"Host config saved.");
            SyncConfigToWeb();
        } else {
            PostStatus(L"error", L"Failed to save host config.");
        }
        break;
    case IncomingMessageKind::Ping:
        PostStatus(L"info", L"Received ping from desktop shell.");
        break;
    case IncomingMessageKind::Unknown:
    default:
        PostStatus(L"warn", L"Unhandled message type from desktop shell.");
        break;
    }
}

void MainFrame::PostStatus(const std::wstring& level, const std::wstring& message) {
    webview_host_.SendJson(bridge_.BuildStatusMessage({level, message}));
}

std::wstring MainFrame::ResolveDesktopShellUrl() const {
    const std::filesystem::path shellPath = std::filesystem::path(MONEYAPP_REPO_ROOT) / "web" / "desktop-shell" / "index.html";
    return PathToFileUrl(shellPath);
}

std::wstring MainFrame::PathToFileUrl(const std::filesystem::path& path) {
    std::wstring url = path.wstring();
    for (wchar_t& ch : url) {
        if (ch == L'\\') {
            ch = L'/';
        }
    }
    if (!url.empty() && url[0] != L'/') {
        url = L"/" + url;
    }
    return L"file://" + url;
}

}  // namespace moneyapp
