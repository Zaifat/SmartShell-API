; Установщик SmartShell Bridge (Inno Setup 6)
; Сборка: ISCC.exe /DAppVersion=2.3.1 build\installer.iss   (см. build.ps1)

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppName "SmartShell Bridge"
#define AppExe "SmartShellBridge.exe"
#define AppPublisher "Zaifat"
#define AppURL "https://github.com/Zaifat/SmartShell-API"

[Setup]
AppId={{6C1F3E2A-8B4D-4F5E-9A7C-2D3B1E0F5A61}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL=https://t.me/zaifat
AppUpdatesURL={#AppURL}/releases
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppName} — установщик
; По умолчанию — установка для текущего пользователя без прав администратора
; (в %LOCALAPPDATA%\Programs). В окне выбора можно установить для всех.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
SetupIconFile=app.ico
WizardStyle=modern
WizardSizePercent=110
OutputDir=..\dist
OutputBaseFilename=SmartShellBridge-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
CloseApplications=force
RestartApplications=no
ShowLanguageDialog=no

[Languages]
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
ru.TaskAutostart=Запускать вместе с Windows (рекомендуется)
en.TaskAutostart=Start with Windows (recommended)
ru.TaskGroupStart=Запуск:
en.TaskGroupStart=Startup:
ru.RunApp=Запустить {#AppName}
en.RunApp=Launch {#AppName}
ru.DeleteData=Удалить также настройки и журналы программы?%n%n(логины, токены, привязки устройств — %1)%n%nНажмите «Нет», если планируете установить программу снова.
en.DeleteData=Also delete settings and logs?%n%n(%1)%n%nChoose "No" if you plan to reinstall.

[Tasks]
Name: "autostart"; Description: "{cm:TaskAutostart}"; GroupDescription: "{cm:TaskGroupStart}"
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\SmartShellBridge\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
; старые файлы прошлых версий (на случай изменения состава библиотек)
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
; Автозапуск — только если пользователь отметил пункт в установщике
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "SmartShellBridge"; \
  ValueData: """{app}\{#AppExe}"" --minimized"; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:RunApp}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
procedure StopRunningApp();
var
  ResultCode: Integer;
  Cmd: String;
begin
  // Сначала просим программу закрыться самой (вместе с окном панели)
  if FileExists(ExpandConstant('{app}\{#AppExe}')) then
    Exec(ExpandConstant('{app}\{#AppExe}'), '--quit', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  // Затем на всякий случай останавливаем только копию программы из папки установки
  // (портативные копии в других папках не трогаем).
  Cmd := '-NoProfile -NonInteractive -Command "Get-Process SmartShellBridge -ErrorAction SilentlyContinue | ' +
         'Where-Object { $_.Path -like ''' + ExpandConstant('{app}') + '\*'' } | Stop-Process -Force"';
  Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'), Cmd, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Sleep(700);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  // при обновлении — остановить запущенную копию, чтобы заменить файлы
  StopRunningApp();
  Result := '';
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir, RunValue: String;
begin
  if CurUninstallStep = usUninstall then
    StopRunningApp();
  if CurUninstallStep = usPostUninstall then
  begin
    // автозапуск мог быть включён из самой программы — убираем, если он указывает на эту установку
    if RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'SmartShellBridge', RunValue) then
      if Pos(Lowercase(ExpandConstant('{app}')), Lowercase(RunValue)) > 0 then
        RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'SmartShellBridge');
    DataDir := ExpandConstant('{userappdata}\SmartShellBridge');
    if DirExists(DataDir) and not UninstallSilent then
      if MsgBox(FmtMessage(CustomMessage('DeleteData'), [DataDir]), mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
        DelTree(DataDir, True, True, True);
  end;
end;
