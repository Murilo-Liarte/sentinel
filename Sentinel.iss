; -----------------------------------------------------------------------------
; Sentinel.iss — Inno Setup Script for Sentinel
; =============================================
; Creates a consumer-grade multilingual Windows Setup Wizard:
;   - User-level install (%LOCALAPPDATA%\Programs\Sentinel) — NO ADMIN PROMPT NEEDED
;   - Multilingual wizard (Portuguese BR default, English, Spanish)
;   - Desktop & Start Menu shortcuts with high-res icon
;   - Silent upgrade support for in-app auto-updater (/SILENT /CLOSEAPPLICATIONS)
;   - Clean uninstaller registered in Windows Settings > Installed Apps
; -----------------------------------------------------------------------------

#define MyAppName "Sentinel"
#define MyAppVersion "1.0.2"
#define MyAppPublisher "Sentinel"
#define MyAppExeName "Sentinel.exe"
#define MyAppAssocName MyAppName + " File"

[Setup]
; Unique AppId GUID for Sentinel
AppId={{A5B6AC5C-CDEB-4F5F-A350-A6883F539B55}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Lowest privileges = installs into user profile without UAC Administrator elevation
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=Sentinel-Setup
SetupIconFile=sentinel.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
CloseApplicationsFilter={#MyAppExeName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "styles.qss"; DestDir: "{app}"; Flags: ignoreversion
Source: "sentinel.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\sentinel.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\sentinel.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
