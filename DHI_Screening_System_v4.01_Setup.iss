; DHI Screening Analysis System v4.01 - Inno Setup Script
; Yili Liquid Milk Research Institute
; Copyright (C) 2025 Yili Liquid Milk Research Institute

; 强制使用UTF-8编码
#pragma codepage(65001)

#define MyAppName "DHI Screening Assistant"
#define MyAppNameChinese "DHI筛查助手"
#define MyAppVersion "4.02"
#define MyAppPublisher "Yili Liquid Milk Research Institute"
#define MyAppURL "https://github.com/Barton0411/dhi_screening"
#define MyAppExeName "DHI_Screening_System.exe"
#define MyAppDescription "DHI Data Analysis and Cattle Health Monitoring System"

[Setup]
; Application Basic Information
AppId={{B6F5E7D4-8A2C-4F1B-9E3D-7A6C8B9D0E1F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright (C) 2025 {#MyAppPublisher}

; Installation Settings
DefaultDirName={autopf}\DHI_Screening_Assistant
DefaultGroupName=DHI Screening Assistant
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer
OutputBaseFilename=DHI_Screening_System_v{#MyAppVersion}_Setup
SetupIconFile=whg3r-qi1nv-001.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; System Requirements
MinVersion=6.1
ArchitecturesAllowed=x86 x64 arm64
ArchitecturesInstallIn64BitMode=x64 arm64

; Permission Settings
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Uninstall Settings
UninstallDisplayIcon={app}\whg3r-qi1nv-001.ico
UninstallDisplayName={#MyAppName} v{#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Main Program Folder (onedir mode complete folder)
Source: "dist\DHI_Screening_System\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Icon file - ensure it's copied
Source: "whg3r-qi1nv-001.ico"; DestDir: "{app}"; Flags: ignoreversion
; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Start Menu Program Group
Name: "{group}\DHI Screening Assistant"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\whg3r-qi1nv-001.ico"
Name: "{group}\Uninstall DHI Screening Assistant"; Filename: "{uninstallexe}"

; Desktop Shortcut - default checked
Name: "{autodesktop}\DHI Screening Assistant"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\whg3r-qi1nv-001.ico"; Tasks: desktopicon

[Run]
; Option to run program after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,DHI Screening Assistant}"; Flags: nowait postinstall skipifsilent

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
    if MsgBox('An old version is detected. Do you want to continue installing the new version?', mbConfirmation, MB_YESNO) = IDNO then
      Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Post-installation processing
  end;
end;
