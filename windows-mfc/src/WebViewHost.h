#pragma once

#include <functional>
#include <string>

#include <Windows.h>
#include <wrl.h>

#include <WebView2.h>

namespace moneyapp {

class WebViewHost {
public:
    using MessageCallback = std::function<void(const std::wstring&)>;
    using ReadyCallback = std::function<void()>;
    using StatusCallback = std::function<void(const std::wstring&)>;

    bool Initialize(HWND parentWindow, const std::wstring& initialUrl);
    void Resize();
    void SendJson(const std::wstring& jsonMessage) const;

    void SetMessageCallback(MessageCallback callback);
    void SetReadyCallback(ReadyCallback callback);
    void SetStatusCallback(StatusCallback callback);

private:
    HWND parent_window_ = nullptr;
    std::wstring initial_url_;
    MessageCallback on_message_;
    ReadyCallback on_ready_;
    StatusCallback on_status_;

    Microsoft::WRL::ComPtr<ICoreWebView2Controller> controller_;
    Microsoft::WRL::ComPtr<ICoreWebView2> webview_;
    EventRegistrationToken message_token_{};
    EventRegistrationToken navigation_token_{};
};

}  // namespace moneyapp
