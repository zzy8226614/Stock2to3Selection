#include "HostConfigStore.h"

#include <cstdlib>
#include <fstream>
#include <string>

namespace moneyapp {

std::filesystem::path HostConfigStore::ResolveBaseDirectory() {
    if (const wchar_t* appData = _wgetenv(L"LOCALAPPDATA")) {
        return std::filesystem::path(appData) / "MoneyAPPDesktop";
    }
    return std::filesystem::temp_directory_path() / "MoneyAPPDesktop";
}

std::filesystem::path HostConfigStore::ResolveConfigPath() const {
    return ResolveBaseDirectory() / "host-config.json";
}

HostConfig HostConfigStore::Load() const {
    HostConfig config;
    const std::filesystem::path path = ResolveConfigPath();
    if (!std::filesystem::exists(path)) {
        return config;
    }

    std::wifstream input(path);
    if (!input.is_open()) {
        return config;
    }

    std::wstring line;
    while (std::getline(input, line)) {
        const size_t splitPos = line.find(L'=');
        if (splitPos == std::wstring::npos) {
            continue;
        }
        const std::wstring key = line.substr(0, splitPos);
        const std::wstring value = line.substr(splitPos + 1);
        if (key == L"baseUrl" && !value.empty()) {
            config.baseUrl = value;
        } else if (key == L"clientType" && !value.empty()) {
            config.clientType = value;
        }
    }
    return config;
}

bool HostConfigStore::Save(const HostConfig& config) const {
    const std::filesystem::path path = ResolveConfigPath();
    std::error_code error;
    std::filesystem::create_directories(path.parent_path(), error);

    std::wofstream output(path, std::ios::trunc);
    if (!output.is_open()) {
        return false;
    }

    output << L"baseUrl=" << config.baseUrl << L"\n";
    output << L"clientType=" << config.clientType << L"\n";
    return output.good();
}

}  // namespace moneyapp
