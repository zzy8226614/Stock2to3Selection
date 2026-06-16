#pragma once

#include <optional>
#include <string>
#include <string_view>

#include "HostMessageTypes.h"

namespace moneyapp {

class AppHostBridge {
public:
    AppHostBridge() = default;

    std::wstring BuildConfigSyncMessage(const HostConfig& config) const;
    std::wstring BuildRequestLogMessage(const RequestLogEntry& entry) const;
    std::wstring BuildRequestReceiptMessage(const RequestLogEntry& entry) const;
    std::wstring BuildStatusMessage(const HostStatus& status) const;
    std::optional<IncomingWebMessage> ParseIncomingMessage(const std::wstring& rawJson) const;

private:
    static std::wstring EscapeJson(const std::wstring& value);
    static std::optional<std::wstring> ExtractStringField(std::wstring_view json, std::wstring_view fieldName);
};

}  // namespace moneyapp
