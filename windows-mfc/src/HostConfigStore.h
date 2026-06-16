#pragma once

#include <filesystem>

#include "HostMessageTypes.h"

namespace moneyapp {

class HostConfigStore {
public:
    HostConfig Load() const;
    bool Save(const HostConfig& config) const;
    std::filesystem::path ResolveConfigPath() const;

private:
    static std::filesystem::path ResolveBaseDirectory();
};

}  // namespace moneyapp
