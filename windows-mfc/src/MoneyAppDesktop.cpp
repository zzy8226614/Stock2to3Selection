#include <afxwin.h>

#include <atlbase.h>

#include "MainFrame.h"

namespace moneyapp {

class MoneyAppDesktopApp : public CWinApp {
public:
    BOOL InitInstance() override {
        CWinApp::InitInstance();
        AfxEnableControlContainer();

        const HRESULT initResult = OleInitialize(nullptr);
        if (FAILED(initResult)) {
            AfxMessageBox(L"Failed to initialize COM/OLE for WebView2.");
            return FALSE;
        }

        auto* frame = new MainFrame();
        if (!frame->Create(
                nullptr,
                L"二进三选股系统",
                WS_OVERLAPPEDWINDOW,
                CRect(80, 80, 980, 720)
            )) {
            delete frame;
            return FALSE;
        }

        m_pMainWnd = frame;
        frame->ShowWindow(SW_SHOW);
        frame->UpdateWindow();
        return TRUE;
    }

    int ExitInstance() override {
        OleUninitialize();
        return CWinApp::ExitInstance();
    }
};

MoneyAppDesktopApp theApp;

}  // namespace moneyapp
