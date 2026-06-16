#include "WebViewHost.h"

using Microsoft::WRL::Callback;
using Microsoft::WRL::ComPtr;

namespace moneyapp {

bool WebViewHost::Initialize(HWND parentWindow, const std::wstring& initialUrl) {
    parent_window_ = parentWindow;
    initial_url_ = initialUrl;

    const HRESULT hr = CreateCoreWebView2EnvironmentWithOptions(
        nullptr,
        nullptr,
        nullptr,
        Callback<ICoreWebView2CreateCoreWebView2EnvironmentCompletedHandler>(
            [this](HRESULT result, ICoreWebView2Environment* environment) -> HRESULT {
                if (FAILED(result) || environment == nullptr) {
                    if (on_status_) {
                        on_status_(L"Failed to create WebView2 environment.");
                    }
                    return result;
                }

                return environment->CreateCoreWebView2Controller(
                    parent_window_,
                    Callback<ICoreWebView2CreateCoreWebView2ControllerCompletedHandler>(
                        [this](HRESULT controllerResult, ICoreWebView2Controller* controller) -> HRESULT {
                            if (FAILED(controllerResult) || controller == nullptr) {
                                if (on_status_) {
                                    on_status_(L"Failed to create WebView2 controller.");
                                }
                                return controllerResult;
                            }

                            controller_ = controller;
                            controller_->get_CoreWebView2(&webview_);
                            if (!webview_) {
                                if (on_status_) {
                                    on_status_(L"WebView2 core view is unavailable.");
                                }
                                return E_FAIL;
                            }

                            ComPtr<ICoreWebView2Settings> settings;
                            if (SUCCEEDED(webview_->get_Settings(&settings)) && settings) {
                                settings->put_IsScriptEnabled(TRUE);
                                settings->put_AreDevToolsEnabled(TRUE);
                                settings->put_IsWebMessageEnabled(TRUE);
                            }

                            webview_->add_WebMessageReceived(
                                Callback<ICoreWebView2WebMessageReceivedEventHandler>(
                                    [this](ICoreWebView2* sender, ICoreWebView2WebMessageReceivedEventArgs* args) -> HRESULT {
                                        LPWSTR rawMessage = nullptr;
                                        if (SUCCEEDED(args->TryGetWebMessageAsString(&rawMessage)) && rawMessage != nullptr) {
                                            if (on_message_) {
                                                on_message_(rawMessage);
                                            }
                                            CoTaskMemFree(rawMessage);
                                        }
                                        return S_OK;
                                    }
                                ).Get(),
                                &message_token_
                            );

                            webview_->add_NavigationCompleted(
                                Callback<ICoreWebView2NavigationCompletedEventHandler>(
                                    [this](ICoreWebView2*, ICoreWebView2NavigationCompletedEventArgs*) -> HRESULT {
                                        if (on_ready_) {
                                            on_ready_();
                                        }
                                        if (on_status_) {
                                            on_status_(L"Desktop shell loaded.");
                                        }
                                        return S_OK;
                                    }
                                ).Get(),
                                &navigation_token_
                            );

                            Resize();
                            webview_->Navigate(initial_url_.c_str());
                            return S_OK;
                        }
                    ).Get()
                );
            }
        ).Get()
    );

    if (FAILED(hr) && on_status_) {
        on_status_(L"CreateCoreWebView2EnvironmentWithOptions call failed.");
    }
    return SUCCEEDED(hr);
}

void WebViewHost::Resize() {
    if (!controller_ || parent_window_ == nullptr) {
        return;
    }
    RECT bounds{};
    GetClientRect(parent_window_, &bounds);
    controller_->put_Bounds(bounds);
}

void WebViewHost::SendJson(const std::wstring& jsonMessage) const {
    if (webview_) {
        webview_->PostWebMessageAsJson(jsonMessage.c_str());
    }
}

void WebViewHost::SetMessageCallback(MessageCallback callback) {
    on_message_ = std::move(callback);
}

void WebViewHost::SetReadyCallback(ReadyCallback callback) {
    on_ready_ = std::move(callback);
}

void WebViewHost::SetStatusCallback(StatusCallback callback) {
    on_status_ = std::move(callback);
}

}  // namespace moneyapp
