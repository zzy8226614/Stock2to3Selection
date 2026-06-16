#pragma once

#include <string>
#include <string_view>

namespace moneyapp {

enum class IncomingMessageKind {
    Unknown,
    RequestLog,
    ConfigSave,
    Ping,
};

struct HostConfig {
    std::wstring baseUrl = L"http://47.107.125.248:8080/";
    std::wstring clientType = L"windows-mfc";
};

struct RequestLogEntry {
    std::wstring path;
    std::wstring method;
    std::wstring startedAt;
    std::wstring baseUrl;
};

struct IncomingWebMessage {
    IncomingMessageKind kind = IncomingMessageKind::Unknown;
    std::wstring rawJson;
    HostConfig config;
    RequestLogEntry requestLog;
};

struct HostStatus {
    std::wstring level;
    std::wstring message;
};

}  // namespace moneyapp
