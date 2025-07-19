; DHI Screening Analysis System v4.01 - Inno Setup Script
; Yili Liquid Milk Research Institute
; Copyright (C) 2025 Yili Liquid Milk Research Institute

#define MyAppName "DHI Screening Analysis System"
#define MyAppNameChinese "DHI筛查分析系统"
#define MyAppVersion "4.01"
#define MyAppPublisher "Yili Liquid Milk Research Institute"
#define MyAppURL "https://github.com/Barton0411/dhi_screening"
#define MyAppExeName "DHI筛查助手.exe"
#define MyAppDescription "DHI Data Analysis and Cattle Health Monitoring System"

[Setup]
; Application Basic Information
AppId={{B6F5E7D4-8A2C-4F1B-9E3D-7A6C8B9D0E1F}
AppName={#MyAppNameChinese}
AppVersion={#MyAppVersion}
AppVerName={#MyAppNameChinese} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright (C) 2025 {#MyAppPublisher}

; Installation Settings
DefaultDirName={autopf}\{#MyAppNameChinese}
DefaultGroupName={#MyAppNameChinese}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer
OutputBaseFilename=DHI_Screening_System_v{#MyAppVersion}_Setup
SetupIconFile=whg3r-qi1nv-001.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; System Requirements - 兼容更多Windows系统
MinVersion=6.1
ArchitecturesAllowed=x86 x64
ArchitecturesInstallIn64BitMode=x64

; Permission Settings
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Uninstall Settings
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppNameChinese} v{#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main Program Folder (onedir mode complete folder)
Source: "dist\DHI筛查助手\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "操作说明.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "Operation_Manual.md"
; Configuration Files
Source: "config.yaml"; DestDir: "{app}"; Flags: ignoreversion
Source: "rules.yaml"; DestDir: "{app}"; Flags: ignoreversion
; Icon File
Source: "whg3r-qi1nv-001.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu Program Group
Name: "{group}\{#MyAppNameChinese}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\whg3r-qi1nv-001.ico"
Name: "{group}\Operation Manual"; Filename: "{app}\Operation_Manual.md"
Name: "{group}\Uninstall {#MyAppNameChinese}"; Filename: "{uninstallexe}"

; Desktop Shortcut
Name: "{autodesktop}\{#MyAppNameChinese}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\whg3r-qi1nv-001.ico"; Tasks: desktopicon

[Run]
; Option to run program after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppNameChinese, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Delete user data folders when uninstalling (optional)
Type: filesandordirs; Name: "{app}\uploads"
Type: filesandordirs; Name: "{app}\exports"
Type: filesandordirs; Name: "{app}\temp"
Type: filesandordirs; Name: "{app}\*.log"

[Code]
// Custom Installation Logic
function InitializeSetup(): Boolean;
begin
  Result := True;
  // Check if old version is already installed
  if RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{B6F5E7D4-8A2C-4F1B-9E3D-7A6C8B9D0E1F}_is1') then
  begin
    if MsgBox('An old version of DHI Screening Analysis System is detected. Do you want to continue installing the new version?', mbConfirmation, MB_YESNO) = IDNO then
      Result := False;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  // Pre-installation preparation
  // You can add dependency checks, service stops, etc. here
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Post-installation processing
    // You can add registry settings, configuration file initialization, etc. here
  end;
end; 