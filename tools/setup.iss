[Setup]
AppName=OpenNumismat
AppId=OpenNumismat
AppVersion=1.4.9
DefaultDirName={pf}\OpenNumismat
DefaultGroupName=OpenNumismat
UninstallDisplayIcon={app}\OpenNumismat.exe
OutputDir="."
OutputBaseFilename="OpenNumismat-1.4.9"
AllowNoIcons=yes
AppCopyright=Copyright 2011-2014 by Vitaly Ignatov
AppPublisher=Janis

[Languages]
Name: en; MessagesFile: "compiler:Default.isl"; InfoBeforeFile: license_en.txt
Name: ru; MessagesFile: "compiler:Languages\Russian.isl"; InfoBeforeFile: license_ru.txt
Name: uk; MessagesFile: "compiler:Languages\Ukrainian.isl"; InfoBeforeFile: license_uk.txt
Name: es; MessagesFile: "compiler:Languages\Spanish.isl"; InfoBeforeFile: license_es.txt
Name: hu; MessagesFile: "compiler:Languages\Hungarian.isl"; InfoBeforeFile: license_en.txt
Name: pt; MessagesFile: "compiler:Languages\Portuguese.isl"; InfoBeforeFile: license_pt.txt
Name: de; MessagesFile: "compiler:Languages\German.isl"; InfoBeforeFile: license_de.txt
Name: el; MessagesFile: "compiler:Languages\Greek.isl"; InfoBeforeFile: license_en.txt
Name: cs; MessagesFile: "compiler:Languages\Czech.isl"; InfoBeforeFile: license_en.txt

[CustomMessages]
en.sendReport=Send a reports to author's web-site if any error occured
ru.sendReport=Посылать отчет разработчику при возникновении ошибки
uk.sendReport=Відправляти звіт про помилки автору
es.sendReport=Enviar un informe al autor del sitio web si cualquier error
hu.sendReport=Hiba elkuldese a keszitonek
pt.sendReport=Enviar relatorios para o autor do web-site se algum erro ocorreu
de.sendReport=Send a reports to author's web-site if any error occured
el.sendReport=Send a reports to author's web-site if any error occured
cs.sendReport=Send a reports to author's web-site if any error occured

[Files]
Source: "..\build\exe.win32-3.2\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "..\build\exe.win32-3.2\db\demo_en.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "demo.db"; Languages: en; Flags: onlyifdoesntexist
Source: "..\build\exe.win32-3.2\db\demo_ru.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "demo.db"; Languages: ru; Flags: onlyifdoesntexist
Source: "..\build\exe.win32-3.2\db\demo_uk.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "demo.db"; Languages: uk; Flags: onlyifdoesntexist
Source: "..\build\exe.win32-3.2\db\demo_es.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "demo.db"; Languages: es; Flags: onlyifdoesntexist
Source: "..\build\exe.win32-3.2\db\demo_hu.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "demo.db"; Languages: hu; Flags: onlyifdoesntexist
Source: "..\build\exe.win32-3.2\db\demo_pt.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "demo.db"; Languages: pt; Flags: onlyifdoesntexist
Source: "..\build\exe.win32-3.2\db\demo_de.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "demo.db"; Languages: de; Flags: onlyifdoesntexist
Source: "..\build\exe.win32-3.2\db\demo_el.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "demo.db"; Languages: el; Flags: onlyifdoesntexist
Source: "..\build\exe.win32-3.2\db\demo_cs.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "demo.db"; Languages: cs; Flags: onlyifdoesntexist
Source: "..\build\exe.win32-3.2\db\reference_en.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: en; Flags: confirmoverwrite
Source: "..\build\exe.win32-3.2\db\reference_ru.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: ru; Flags: confirmoverwrite
Source: "..\build\exe.win32-3.2\db\reference_uk.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: uk; Flags: confirmoverwrite
Source: "..\build\exe.win32-3.2\db\reference_es.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: es; Flags: confirmoverwrite
Source: "..\build\exe.win32-3.2\db\reference_hu.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: hu; Flags: confirmoverwrite
Source: "..\build\exe.win32-3.2\db\reference_pt.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: pt; Flags: confirmoverwrite
Source: "..\build\exe.win32-3.2\db\reference_de.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: de; Flags: confirmoverwrite
Source: "..\build\exe.win32-3.2\db\reference_el.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: el; Flags: confirmoverwrite
Source: "..\build\exe.win32-3.2\db\reference_cs.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: cs; Flags: confirmoverwrite

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
