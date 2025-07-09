; DHI筛查分析系统 v3.0 - Inno Setup安装脚本
; 伊利液奶奶科院
; Copyright (C) 2025 伊利液奶奶科院 版权所有

#define MyAppName "DHI筛查分析系统"
#define MyAppVersion "3.0"
#define MyAppPublisher "伊利液奶奶科院"
#define MyAppURL "https://github.com/Barton0411/dhi_screening"
#define MyAppExeName "DHI_Screening_System_v3.0.exe"
#define MyAppDescription "DHI数据分析与牛群健康监测系统"

[Setup]
; 应用程序基本信息
AppId={{B6F5E7D4-8A2C-4F1B-9E3D-7A6C8B9D0E1F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright (C) 2025 {#MyAppPublisher}

; 安装设置
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer
OutputBaseFilename={#MyAppName}_v{#MyAppVersion}_Setup
SetupIconFile=whg3r-qi1nv-001.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; 系统要求
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; 权限设置
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; 卸载设置
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} v{#MyAppVersion}

[Languages]
Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; 主程序文件夹（onedir模式的完整文件夹）
Source: "dist\DHI_Screening_System_v3.0\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; 说明文档
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "DHI_精准筛查助手-操作说明.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "需求说明.md"; DestDir: "{app}"; Flags: ignoreversion
; 配置文件
Source: "config.yaml"; DestDir: "{app}"; Flags: ignoreversion
Source: "rules.yaml"; DestDir: "{app}"; Flags: ignoreversion
; 图标文件
Source: "whg3r-qi1nv-001.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; 开始菜单程序组
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\whg3r-qi1nv-001.ico"
Name: "{group}\操作说明"; Filename: "{app}\DHI_精准筛查助手-操作说明.md"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"

; 桌面快捷方式
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\whg3r-qi1nv-001.ico"; Tasks: desktopicon

; 快速启动栏（Windows 7及以下）
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\whg3r-qi1nv-001.ico"; Tasks: quicklaunchicon

[Run]
; 安装完成后运行程序选项
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时删除用户数据文件夹（可选）
Type: filesandordirs; Name: "{app}\uploads"
Type: filesandordirs; Name: "{app}\exports"
Type: filesandordirs; Name: "{app}\temp"
Type: filesandordirs; Name: "{app}\*.log"

[Messages]
; 自定义中文消息
chinese.WelcomeLabel1=欢迎使用 [name] 安装向导
chinese.WelcomeLabel2=这将在您的计算机上安装 [name/ver]。%n%n伊利液奶奶科院专业DHI数据分析系统，提供牛群健康监测和慢性乳房炎筛查功能。%n%n建议您在继续之前关闭所有其他应用程序。
chinese.LicenseLabel=安装前请仔细阅读许可协议
chinese.SelectDirLabel=安装向导将安装 [name] 到以下文件夹
chinese.SelectComponentsLabel=请选择要安装的组件
chinese.ReadyLabel=安装向导现在准备开始在您的计算机上安装 [name]
chinese.InstallingLabel=安装向导正在您的计算机上安装 [name]，请稍候
chinese.FinishedLabel=[name] 安装完成
chinese.ClickFinish=单击"完成"退出安装向导

[Code]
// 自定义安装逻辑
function InitializeSetup(): Boolean;
begin
  Result := True;
  // 检查是否已安装旧版本
  if RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{B6F5E7D4-8A2C-4F1B-9E3D-7A6C8B9D0E1F}_is1') then
  begin
    if MsgBox('检测到已安装旧版本的DHI筛查分析系统。是否要继续安装新版本？', mbConfirmation, MB_YESNO) = IDNO then
      Result := False;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  // 安装前准备工作
  // 这里可以添加检查依赖、停止服务等逻辑
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 安装完成后的处理
    // 可以在这里添加注册表设置、配置文件初始化等
  end;
end; 