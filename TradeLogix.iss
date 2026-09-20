#define MyAppName "TradeLogix"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "TradeLogix"
#define MyAppExeName "TradeLogix.exe"

[Setup]
AppId={{8D4F6E71-8A77-4C88-B9E0-123456789001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\TradeLogix
DefaultGroupName=TradeLogix
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer
OutputBaseFilename=TradeLogix-Setup-1.0.0
SetupIconFile=assets\tradelogix.ico
UninstallDisplayIcon={app}\TradeLogix.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "dist\TradeLogix\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\TradeLogix"; Filename: "{app}\TradeLogix.exe"; WorkingDir: "{app}"; IconFilename: "{app}\TradeLogix.exe"
Name: "{group}\TradeLogix"; Filename: "{app}\TradeLogix.exe"; WorkingDir: "{app}"; IconFilename: "{app}\TradeLogix.exe"

[Run]
Filename: "{app}\TradeLogix.exe"; Description: "Launch TradeLogix"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\backups"
; Keep the user's journal data and screenshots on uninstall by design.
