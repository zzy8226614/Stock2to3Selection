#include "AppHostBridge.h"

#include <string_view>

namespace moneyapp {

std::wstring AppHostBridge::EscapeJson(const std::wstring& value) {
    std::wstring escaped;
    escaped.reserve(value.size());
    for (const wchar_t ch : value) {
        switch (ch) {
        case L'\\':
            escaped += L"\\\\";
            break;
        case L'"':
            escaped += L"\\\"";
            break;
        case L'\n':
            escaped += L"\\n";
            break;
        case L'\r':
            escaped += L"\\r";
            break;
        case L'\t':
            escaped += L"\\t";
            break;
        default:
            escaped += ch;
            break;
        }
    }
    return escaped;
}

std::optional<std::wstring> AppHostBridge::ExtractStringField(
    const std::wstring_view json,
    const std::wstring_view fieldName
) {
    const std::wstring needle = std::wstring(L"\"") + std::wstring(fieldName) + L"\"";
    const size_t keyPos = json.find(needle);
    if (keyPos == std::wstring_view::npos) {
        return std::nullopt;
    }
    const size_t colonPos = json.find(L':', keyPos + needle.size());
    if (colonPos == std::wstring_view::npos) {
        return std::nullopt;
    }
    const size_t valueStart = json.find(L'"', colonPos + 1);
    if (valueStart == std::wstring_view::npos) {
        return std::nullopt;
    }
    const size_t valueEnd = json.find(L'"', valueStart + 1);
    if (valueEnd == std::wstring_view::npos || valueEnd <= valueStart) {
        return std::nullopt;
    }
    return std::wstring(json.substr(valueStart + 1, valueEnd - valueStart - 1));
}

std::wstring AppHostBridge::BuildConfigSyncMessage(const HostConfig& config) const {
    return L"{\"type\":\"host.config.sync\",\"payload\":{\"baseUrl\":\"" + EscapeJson(config.baseUrl) +
        L"\",\"clientType\":\"" + EscapeJson(config.clientType) + L"\"}}";
}

std::wstring AppHostBridge::BuildRequestLogMessage(const RequestLogEntry& entry) const {
    return L"{\"type\":\"web.request.log\",\"payload\":{\"path\":\"" + EscapeJson(entry.path) +
        L"\",\"method\":\"" + EscapeJson(entry.method) + L"\",\"startedAt\":\"" + EscapeJson(entry.startedAt) +
        L"\",\"baseUrl\":\"" + EscapeJson(entry.baseUrl) + L"\"}}";
}

std::wstring AppHostBridge::BuildRequestReceiptMessage(const RequestLogEntry& entry) const {
    return L"{\"type\":\"host.request.received\",\"payload\":{\"path\":\"" + EscapeJson(entry.path) +
        L"\",\"method\":\"" + EscapeJson(entry.method) + L"\",\"startedAt\":\"" + EscapeJson(entry.startedAt) +
        L"\",\"baseUrl\":\"" + EscapeJson(entry.baseUrl) + L"\"}}";
}

std::wstring AppHostBridge::BuildStatusMessage(const HostStatus& status) const {
    return L"{\"type\":\"host.status\",\"payload\":{\"level\":\"" + EscapeJson(status.level) +
        L"\",\"message\":\"" + EscapeJson(status.message) + L"\"}}";
}

std::optional<IncomingWebMessage> AppHostBridge::ParseIncomingMessage(const std::wstring& rawJson) const {
    const auto type = ExtractStringField(rawJson, L"type");
    if (!type.has_value()) {
        return std::nullopt;
    }

    IncomingWebMessage message;
    message.rawJson = rawJson;
    if (*type == L"web.request.log") {
        message.kind = IncomingMessageKind::RequestLog;
        message.requestLog.path = ExtractStringField(rawJson, L"path").value_or(L"");
        message.requestLog.method = ExtractStringField(rawJson, L"method").value_or(L"");
        message.requestLog.startedAt = ExtractStringField(rawJson, L"startedAt").value_or(L"");
        message.requestLog.baseUrl = ExtractStringField(rawJson, L"baseUrl").value_or(L"");
        return message;
    }

    if (*type == L"host.config.save") {
        message.kind = IncomingMessageKind::ConfigSave;
        message.config.baseUrl = ExtractStringField(rawJson, L"baseUrl").value_or(L"http://47.107.125.248:8080/");
        message.config.clientType = ExtractStringField(rawJson, L"clientType").value_or(L"windows-mfc");
        return message;
    }

    if (*type == L"host.ping") {
        message.kind = IncomingMessageKind::Ping;
        return message;
    }

    return message;
}

}  // namespace moneyapp
