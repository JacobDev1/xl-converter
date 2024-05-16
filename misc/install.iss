; Inno Setup 6.2.2 script
; /skip_deps - skips the installation of vc_redist

#define MyAppName "XL Converter"
#define MyAppVersion "0.9"
#define MyAppPublisher "Code Poems"
#define MyAppURL "https://codepoems.eu"
#define MyAppExeName "xl-converter.exe"

[Setup]
AppId={{19959888-4928-4F51-9C9F-DE681EC27DAA}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
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

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Files]
Source: "xl-converter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "..\misc\VC_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Code]
var
  NoDeps: Boolean;

function InitializeSetup: Boolean;
var
  i: Integer;
begin
  NoDeps := False;
  for i := 1 to ParamCount do
  begin
    if ParamStr(i) = '/skip_deps' then
    begin
      NoDeps := True;
      Break;
    end;
  end;
  Result := True;
end;

function InstallDeps: Boolean;
begin
  Result := not NoDeps;
end;

[Run]
Filename: "{tmp}\VC_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Installing Microsoft Redistributable..."; Check: InstallDeps
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent