@echo off
setlocal

set VS2008_VCVARS="C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\vcvarsall.bat"
if not exist %VS2008_VCVARS% (
  echo VS2008 vcvarsall.bat not found.
  exit /b 1
)

call %VS2008_VCVARS% x86
if errorlevel 1 exit /b 1

set ROOT=%~dp0
set SRC=%ROOT%legacy-src\MoneyAppDesktopLegacy.cpp
set OUTDIR=%ROOT%build-vs2008

if not exist "%OUTDIR%" mkdir "%OUTDIR%"

cl /nologo /EHsc /MD /D_AFXDLL /DUNICODE /D_UNICODE ^
  /Fo"%OUTDIR%\\" /Fe"%OUTDIR%\\MoneyAppDesktopLegacy.exe" ^
  "%SRC%" ^
  /link /SUBSYSTEM:WINDOWS /MACHINE:X86 ole32.lib oleaut32.lib uuid.lib user32.lib gdi32.lib advapi32.lib shlwapi.lib

if errorlevel 1 exit /b 1

echo Build output: %OUTDIR%\MoneyAppDesktopLegacy.exe
exit /b 0
