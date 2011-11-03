[Setup]
AppName=OpenNumismat
AppId=OpenNumismat
AppVersion=0.9
DefaultDirName={pf}\OpenNumismat
DefaultGroupName=OpenNumismat
UninstallDisplayIcon={app}\OpenNumismat.exe
OutputDir="."
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputBaseFilename="OpenNumismat-0.9-amd64"
AllowNoIcons=yes
AppCopyright=Copyright 2011 by Vitaly Ignatov

[Languages]
Name: en; MessagesFile: "compiler:Default.isl"; InfoBeforeFile: license_en.txt
Name: ru; MessagesFile: "compiler:Languages\Russian.isl"; InfoBeforeFile: license_ru.txt

[Messages]
en.BeveledLabel=English
ru.BeveledLabel=Russian

[CustomMessages]
en.sendReport=Send a reports to author's web-site if any error occured
ru.sendReport=Посылать отчет разработчику при возникновении ошибки

[Files]
Source: "dist\*"; DestDir: "{app}"; Flags: recursesubdirs
Source: "..\db\demo_en.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "demo.db"; Languages: en; Flags: confirmoverwrite
Source: "..\db\demo_ru.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "demo.db"; Languages: ru; Flags: confirmoverwrite
Source: "reference_en.db"; DestDir: "{app}"
Source: "reference_en.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.db"; Languages: en
Source: "reference_ru.db"; DestDir: "{app}"
Source: "reference_ru.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.db"; Languages: ru

[Dirs]
Name: "{userdocs}\OpenNumismat\backup"

[Registry]
Root: HKCU; Subkey: "Software\Janis"; Flags: uninsdeletekeyifempty
Root: HKCU; Subkey: "Software\Janis\OpenNumismat"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Janis\OpenNumismat\mainwindow"; ValueType: string; ValueName: "error"; ValueData: "true"; Tasks: sendreport

[Icons]
Name: "{group}\OpenNumismat"; Filename: "{app}\OpenNumismat.exe"
Name: "{group}\Uninstall OpenNumismat"; Filename: "{uninstallexe}"
Name: "{userdesktop}\OpenNumismat"; Filename: "{app}\OpenNumismat.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\OpenNumismat"; Filename: "{app}\OpenNumismat.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\OpenNumismat.exe"; Flags: postinstall nowait skipifsilent

[Tasks]
Name: sendreport; Description: "{cm:sendReport}"
Name: desktopicon; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: quicklaunchicon; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
