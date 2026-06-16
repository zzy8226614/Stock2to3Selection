#pragma once

#include <filesystem>

#include <afxwin.h>

#include "AppHostBridge.h"
#include "HostConfigStore.h"
#include "WebViewHost.h"

namespace moneyapp {

class MainFrame : public CFrameWnd {
public:
    MainFrame();

protected:
    afx_msg int OnCreate(LPCREATESTRUCT lpCreateStruct);
    afx_msg void OnSize(UINT type, int cx, int cy);
    afx_msg void OnClose();
    DECLARE_MESSAGE_MAP()

private:
    CWnd browser_container_;
    AppHostBridge bridge_;
    HostConfigStore config_store_;
    HostConfig config_;
    WebViewHost webview_host_;

    void SyncConfigToWeb();
    void HandleWebMessage(const std::wstring& rawJson);
    void PostStatus(const std::wstring& level, const std::wstring& message);
    std::wstring ResolveDesktopShellUrl() const;
    static std::wstring PathToFileUrl(const std::filesystem::path& path);
};

}  // namespace moneyapp
