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

[Languages]
Name: en; MessagesFile: "compiler:Default.isl"
Name: ru; MessagesFile: "compiler:Languages\Russian.isl"

[Messages]
en.BeveledLabel=English
ru.BeveledLabel=Russian

[Files]
Source: "dist\*"; DestDir: "{app}"
Source: "dist\icons\*"; DestDir: "{app}\icons"
Source: "dist\imageformats\*"; DestDir: "{app}\imageformats"
Source: "dist\sqldrivers/*"; DestDir: "{app}/sqldrivers"
Source: "..\db\demo.db"; DestDir: "{userdocs}\OpenNumismat"; Flags: confirmoverwrite
Source: "..\db\reference_en.db"; DestDir: "{app}"
Source: "..\db\reference_en.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.db"; Languages: en
Source: "..\db\reference_ru.db"; DestDir: "{app}"
Source: "..\db\reference_ru.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.db"; Languages: ru

[Dirs]
Name: "{userdocs}\OpenNumismat\backup"

[Registry]
Root: HKCU; Subkey: "Software\Janis"; Flags: uninsdeletekeyifempty
Root: HKCU; Subkey: "Software\Janis\OpenNumismat"; Flags: uninsdeletekey

[Icons]
Name: "{commondesktop}\OpenNumismat"; Filename: "{app}\OpenNumismat.exe"; WorkingDir: "{app}"
Name: "{group}\OpenNumismat"; Filename: "{app}\OpenNumismat.exe"; WorkingDir: "{app}"
Name: "{group}\Uninstall OpenNumismat"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\OpenNumismat.exe"; Flags: postinstall nowait skipifsilent
