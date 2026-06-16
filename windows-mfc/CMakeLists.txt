cmake_minimum_required(VERSION 3.25)

project(MoneyAppDesktop LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_MFC_FLAG 1)

set(WEBVIEW2_SDK_PATH "$ENV{WEBVIEW2_SDK_PATH}" CACHE PATH "Path to Microsoft Edge WebView2 SDK")

if(NOT EXISTS "${WEBVIEW2_SDK_PATH}/build/native/include/WebView2.h")
    message(FATAL_ERROR "Set WEBVIEW2_SDK_PATH to a valid WebView2 SDK root.")
endif()

get_filename_component(MONEYAPP_REPO_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/.." ABSOLUTE)
string(REPLACE "\\" "\\\\" MONEYAPP_REPO_ROOT_ESCAPED "${MONEYAPP_REPO_ROOT}")

add_executable(MoneyAppDesktop WIN32
    src/AppHostBridge.cpp
    src/HostConfigStore.cpp
    src/MainFrame.cpp
    src/MoneyAppDesktop.cpp
    src/WebViewHost.cpp
)

target_compile_definitions(MoneyAppDesktop PRIVATE
    _AFXDLL
    UNICODE
    _UNICODE
    MONEYAPP_REPO_ROOT=L"${MONEYAPP_REPO_ROOT_ESCAPED}"
)

target_include_directories(MoneyAppDesktop PRIVATE
    src
    "${WEBVIEW2_SDK_PATH}/build/native/include"
)

target_link_directories(MoneyAppDesktop PRIVATE
    "${WEBVIEW2_SDK_PATH}/build/native/x64"
)

target_link_libraries(MoneyAppDesktop PRIVATE
    WebView2LoaderStatic
    Shlwapi
)
