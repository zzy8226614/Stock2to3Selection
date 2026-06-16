using System;
using System.Drawing;
using System.IO;
using System.Windows.Forms;
using Microsoft.Win32;

namespace MoneyAppDesktopWinForms
{
    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            BrowserFeatureControl.EnableBrowserEmulation();
            Application.Run(new MainForm());
        }
    }

    internal sealed class MainForm : Form
    {
        private readonly WebBrowser browser;
        private readonly ToolStripStatusLabel statusLabel;

        public MainForm()
        {
            Text = "二进三选股系统";
            Width = 980;
            Height = 720;
            StartPosition = FormStartPosition.CenterScreen;

            var menu = new MenuStrip();
            var appMenu = new ToolStripMenuItem("应用");
            var refreshItem = new ToolStripMenuItem("刷新页面");
            refreshItem.Click += delegate { browser.Refresh(); };
            var homeItem = new ToolStripMenuItem("打开桌面首页");
            homeItem.Click += delegate { NavigateToShell(); };
            var exitItem = new ToolStripMenuItem("退出");
            exitItem.Click += delegate { Close(); };
            appMenu.DropDownItems.Add(homeItem);
            appMenu.DropDownItems.Add(refreshItem);
            appMenu.DropDownItems.Add(new ToolStripSeparator());
            appMenu.DropDownItems.Add(exitItem);
            menu.Items.Add(appMenu);
            MainMenuStrip = menu;

            browser = new WebBrowser();
            browser.Dock = DockStyle.Fill;
            browser.ScriptErrorsSuppressed = false;
            browser.IsWebBrowserContextMenuEnabled = true;
            browser.WebBrowserShortcutsEnabled = true;
            browser.Navigated += OnNavigated;
            browser.DocumentTitleChanged += OnDocumentTitleChanged;

            var statusStrip = new StatusStrip();
            statusLabel = new ToolStripStatusLabel("正在初始化...");
            statusStrip.Items.Add(statusLabel);

            Controls.Add(browser);
            Controls.Add(statusStrip);
            Controls.Add(menu);

            Load += delegate { NavigateToShell(); };
        }

        private void NavigateToShell()
        {
            browser.Navigate(new Uri(GetShellUrl()));
        }

        private void OnNavigated(object sender, WebBrowserNavigatedEventArgs e)
        {
            statusLabel.Text = "已加载: " + e.Url;
        }

        private void OnDocumentTitleChanged(object sender, EventArgs e)
        {
            if (!string.IsNullOrEmpty(browser.DocumentTitle))
            {
                Text = browser.DocumentTitle + " - 二进三选股系统";
            }
        }

        /// <summary>
        /// Prefer loading <c>web/desktop-shell/index.html</c> from disk (file://), same as the MFC host.
        /// Navigating to a remote URL when the server has no static route or returns 404 causes the legacy
        /// WebBrowser control to show "navigation canceled" and spurious file-download dialogs.
        /// </summary>
        private static string GetShellUrl()
        {
            var exeDir = Path.GetDirectoryName(Application.ExecutablePath);
            if (!string.IsNullOrEmpty(exeDir))
            {
                var sideBySide = Path.Combine(exeDir, "web", "desktop-shell", "index.html");
                if (File.Exists(sideBySide))
                {
                    return new Uri(Path.GetFullPath(sideBySide)).AbsoluteUri;
                }

                for (var dir = exeDir; !string.IsNullOrEmpty(dir); dir = Path.GetDirectoryName(dir))
                {
                    var candidate = Path.Combine(dir, "web", "desktop-shell", "index.html");
                    if (File.Exists(candidate))
                    {
                        return new Uri(Path.GetFullPath(candidate)).AbsoluteUri;
                    }
                }
            }

            return "http://47.107.125.248:8081/desktop-shell/";
        }
    }

    internal static class BrowserFeatureControl
    {
        private const int BrowserEmulationMode = 11001;

        public static void EnableBrowserEmulation()
        {
            try
            {
                var exeName = Path.GetFileName(Application.ExecutablePath);
                using (var key = Registry.CurrentUser.CreateSubKey(
                    @"Software\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_BROWSER_EMULATION"))
                {
                    if (key != null)
                    {
                        key.SetValue(exeName, BrowserEmulationMode, RegistryValueKind.DWord);
                    }
                }
            }
            catch
            {
            }
        }
    }
}
