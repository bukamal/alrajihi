#define MyAppName "Alrajhi Accounting Warehouse"
#define MyAppExeName "AlrajhiAccounting.exe"
#define MyAppVersion "1.0"
#define MyIcon "..\alrajhi_client\assets\brand\app.ico"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\AlrajhiAccountingWarehouse
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile={#MyIcon}
Compression=lzma2
SolidCompression=yes
OutputDir=..\output
OutputBaseFilename=AlrajhiAccountingWarehouse_Release_Setup
WizardStyle=modern
ShowLanguageDialog=yes
PrivilegesRequired=lowest
UsedUserAreasWarning=no

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"

[Files]
Source: "..\dist\AlrajhiAccounting\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "إنشاء اختصار على سطح المكتب"; Flags: unchecked

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\إزالة التثبيت"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "تشغيل {#MyAppName}"; Flags: postinstall nowait skipifsilent
