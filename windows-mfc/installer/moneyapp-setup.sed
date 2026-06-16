[Version]
Class=IEXPRESS
SEDVersion=3

[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=1
UseLongFileName=1
InsideCompressed=1
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=%InstallPrompt%
DisplayLicense=%DisplayLicense%
FinishMessage=%FinishMessage%
TargetName=%TargetName%
FriendlyName=%FriendlyName%
AppLaunched=%AppLaunched%
PostInstallCmd=%PostInstallCmd%
AdminQuietInstCmd=%AdminQuietInstCmd%
UserQuietInstCmd=%UserQuietInstCmd%
SourceFiles=SourceFiles

[Strings]
InstallPrompt=
DisplayLicense=
FinishMessage=MoneyAPP Desktop 安装完成。
TargetName=d:\New_Project\AI_Project\MoneyAPP\windows-mfc\dist\MoneyAppDesktop-Setup.exe
FriendlyName=MoneyAPP Desktop Setup
AppLaunched=cmd.exe /c install.bat
PostInstallCmd=<None>
AdminQuietInstCmd=cmd.exe /c install.bat
UserQuietInstCmd=cmd.exe /c install.bat
FILE0=MoneyAppDesktop.exe
FILE1=index.html
FILE2=app.js
FILE3=bridge.js
FILE4=styles.css
FILE5=install.bat

[SourceFiles]
SourceFiles0=d:\New_Project\AI_Project\MoneyAPP\windows-mfc\installer\staging\

[SourceFiles0]
%FILE0%=
%FILE1%=
%FILE2%=
%FILE3%=
%FILE4%=
%FILE5%=
