#include <afxwin.h>
#include <afxdisp.h>
#include <exdisp.h>
#include <shlwapi.h>
#include <winreg.h>

#pragma comment(lib, "shlwapi.lib")

namespace {

const UINT kBrowserControlId = 1001;
const wchar_t* kDefaultShellUrl = L"http://127.0.0.1:8000/desktop-shell/";

void EnableBrowserEmulation() {
    wchar_t modulePath[MAX_PATH] = {0};
    if (GetModuleFileNameW(NULL, modulePath, MAX_PATH) == 0) {
        return;
    }

    const wchar_t* exeName = PathFindFileNameW(modulePath);
    if (exeName == NULL || exeName[0] == L'\0') {
        return;
    }

    HKEY key = NULL;
    if (RegCreateKeyExW(
            HKEY_CURRENT_USER,
            L"Software\\Microsoft\\Internet Explorer\\Main\\FeatureControl\\FEATURE_BROWSER_EMULATION",
            0,
            NULL,
            REG_OPTION_NON_VOLATILE,
            KEY_SET_VALUE,
            NULL,
            &key,
            NULL
        ) != ERROR_SUCCESS) {
        return;
    }

    DWORD value = 11001;
    RegSetValueExW(
        key,
        exeName,
        0,
        REG_DWORD,
        reinterpret_cast<const BYTE*>(&value),
        sizeof(value)
    );
    RegCloseKey(key);
}

class CBrowserFrame : public CFrameWnd {
public:
    CBrowserFrame()
        : browser_(NULL) {
    }

    virtual ~CBrowserFrame() {
        if (browser_ != NULL) {
            browser_->Release();
            browser_ = NULL;
        }
    }

protected:
    afx_msg int OnCreate(LPCREATESTRUCT lpCreateStruct) {
        if (CFrameWnd::OnCreate(lpCreateStruct) == -1) {
            return -1;
        }

        CRect rect;
        GetClientRect(&rect);
        if (!browser_host_.CreateControl(
                CLSID_WebBrowser,
                NULL,
                WS_CHILD | WS_VISIBLE | WS_CLIPCHILDREN | WS_CLIPSIBLINGS,
                rect,
                this,
                kBrowserControlId
            )) {
            return -1;
        }

        LPUNKNOWN unknown = browser_host_.GetControlUnknown();
        if (unknown == NULL) {
            return -1;
        }

        HRESULT hr = unknown->QueryInterface(IID_IWebBrowser2, reinterpret_cast<void**>(&browser_));
        unknown->Release();
        if (FAILED(hr) || browser_ == NULL) {
            return -1;
        }

        browser_->put_Silent(VARIANT_TRUE);
        Navigate(kDefaultShellUrl);
        return 0;
    }

    afx_msg void OnSize(UINT nType, int cx, int cy) {
        CFrameWnd::OnSize(nType, cx, cy);
        if (browser_host_.GetSafeHwnd() != NULL) {
            browser_host_.MoveWindow(0, 0, cx, cy);
        }
    }

    afx_msg void OnClose() {
        if (browser_ != NULL) {
            browser_->Quit();
        }
        CFrameWnd::OnClose();
    }

    DECLARE_MESSAGE_MAP()

private:
    void Navigate(const wchar_t* url) {
        if (browser_ == NULL || url == NULL) {
            return;
        }

        COleVariant empty;
        BSTR target = ::SysAllocString(url);
        browser_->Navigate(target, &empty, &empty, &empty, &empty);
        ::SysFreeString(target);
    }

    CWnd browser_host_;
    IWebBrowser2* browser_;
};

BEGIN_MESSAGE_MAP(CBrowserFrame, CFrameWnd)
    ON_WM_CREATE()
    ON_WM_SIZE()
    ON_WM_CLOSE()
END_MESSAGE_MAP()

class CMoneyAppDesktopLegacyApp : public CWinApp {
public:
    virtual BOOL InitInstance() {
        CWinApp::InitInstance();
        AfxEnableControlContainer();

        if (!AfxOleInit()) {
            AfxMessageBox(L"Failed to initialize OLE.");
            return FALSE;
        }

        EnableBrowserEmulation();

        CBrowserFrame* frame = new CBrowserFrame();
        if (!frame->Create(
                NULL,
                L"MoneyAPP Desktop Legacy",
                WS_OVERLAPPEDWINDOW,
                CRect(120, 120, 1500, 960)
            )) {
            delete frame;
            return FALSE;
        }

        m_pMainWnd = frame;
        frame->ShowWindow(SW_SHOW);
        frame->UpdateWindow();
        return TRUE;
    }

    virtual int ExitInstance() {
        AfxOleTerm(FALSE);
        return CWinApp::ExitInstance();
    }
};

CMoneyAppDesktopLegacyApp theApp;

}  // namespace
