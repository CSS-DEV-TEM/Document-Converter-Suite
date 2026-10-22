#define MyAppName "Hayleys Excel Converter"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Kaveesha Bandara"
#define MyAppExeName "HayleysExcelConverter.exe"

[Setup]
; Keep this AppId unchanged in future releases.
AppId={{D02B7DB4-32F4-4F9E-A017-648EEA8D476C}

AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
UninstallDisplayName={#MyAppName}

; Install for the current user without administrator privileges.
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\HayleysExcelConverter

DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
UsePreviousAppDir=yes

OutputDir=installer-output
OutputBaseFilename=HayleysExcelConverter-Setup-{#MyAppVersion}

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

UninstallDisplayIcon={app}\{#MyAppExeName}

; Close the running application before replacing its files.
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\HayleysExcelConverter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent