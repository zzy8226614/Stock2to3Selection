@echo off
setlocal

set CSC="C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if not exist %CSC% (
  echo csc.exe not found.
  exit /b 1
)

set ROOT=%~dp0
set OUTDIR=%ROOT%build-winforms
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

%CSC% /nologo /target:winexe /platform:anycpu ^
  /out:"%OUTDIR%\MoneyAppDesktop.exe" ^
  /reference:System.dll ^
  /reference:System.Drawing.dll ^
  /reference:System.Windows.Forms.dll ^
  "%ROOT%winforms-host\MoneyAppDesktopWinForms.cs"

if errorlevel 1 exit /b 1

echo Build output: %OUTDIR%\MoneyAppDesktop.exe
exit /b 0
