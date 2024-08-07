; Inno Setup 6.2.2 script

#define MyAppName "XL Converter"
#define MyAppVersion "0.9"
#define MyAppPublisher "Code Poems"
#define MyAppURL "https://codepoems.eu"
#define MyAppExeName "xl-converter.exe"

[Setup]
AppId={{19959888-4928-4F51-9C9F-DE681EC27DAA}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile="..\LICENSE.txt"
PrivilegesRequired=admin
OutputBaseFilename=xl-converter
SetupIconFile="..\icons\logo.ico"
Compression=lzma2
;Compression=none
SolidCompression=yes
WizardStyle=modern
DisableReadyPage=yes
DisableDirPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "install_vcredist"; Description: "Install Microsoft Redistributable (required)"; GroupDescription: "Dependencies"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Files]
Source: "xl-converter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "..\misc\VC_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Code]
procedure CheckTask(TaskName: String; Checked: Boolean);
var
  TaskIndex: Integer;
begin
  TaskIndex := WizardForm.TasksList.Items.IndexOf(TaskName);
  if TaskIndex <> -1 then
    WizardForm.TasksList.Checked[TaskIndex] := Checked;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpSelectTasks then
    CheckTask('Install Microsoft Redistributable (required)', True);
end;

[Run]
Filename: "{tmp}\VC_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Installing Microsoft Redistributable..."; Check: WizardIsTaskSelected('install_vcredist')
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent