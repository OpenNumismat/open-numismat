﻿[Setup]
AppName=OpenNumismat
AppId=OpenNumismat
AppVersion=1.10.2
DefaultDirName={commonpf}\OpenNumismat
DefaultGroupName=OpenNumismat
UninstallDisplayIcon={app}\OpenNumismat.exe
OutputDir="."
OutputBaseFilename=OpenNumismat-{#SetupSetting('AppVersion')}
AllowNoIcons=yes
AppCopyright=Copyright 2011-2025 by Vitaly Ignatov
AppPublisher=Janis
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: en; MessagesFile: "compiler:Default.isl"; InfoBeforeFile: license_en.txt
Name: ru; MessagesFile: "compiler:Languages\Russian.isl"; InfoBeforeFile: license_ru.txt
Name: uk; MessagesFile: "compiler:Languages\Ukrainian.isl"; InfoBeforeFile: license_uk.txt
Name: es; MessagesFile: "compiler:Languages\Spanish.isl"; InfoBeforeFile: license_es.txt
Name: fr; MessagesFile: "compiler:Languages\French.isl"; InfoBeforeFile: license_fr.txt
Name: hu; MessagesFile: "compiler:Languages\Hungarian.isl"; InfoBeforeFile: license_en.txt
Name: pt; MessagesFile: "compiler:Languages\Portuguese.isl"; InfoBeforeFile: license_pt.txt
Name: de; MessagesFile: "compiler:Languages\German.isl"; InfoBeforeFile: license_de.txt
;Name: el; MessagesFile: "compiler:Languages\Greek.isl"; InfoBeforeFile: license_el.txt
Name: cs; MessagesFile: "compiler:Languages\Czech.isl"; InfoBeforeFile: license_en.txt
Name: it; MessagesFile: "compiler:Languages\Italian.isl"; InfoBeforeFile: license_it.txt
Name: pl; MessagesFile: "compiler:Languages\Polish.isl"; InfoBeforeFile: license_pl.txt
Name: ca; MessagesFile: "compiler:Languages\Catalan.isl"; InfoBeforeFile: license_ca.txt
Name: nl; MessagesFile: "compiler:Languages\Dutch.isl"; InfoBeforeFile: license_nl.txt
Name: bg; MessagesFile: "compiler:Languages\Bulgarian.isl"; InfoBeforeFile: license_bg.txt
;Name: lv; MessagesFile: "compiler:Languages\Latvian.isl"; InfoBeforeFile: license_lv.txt
Name: tr; MessagesFile: "compiler:Languages\Turkish.isl"; InfoBeforeFile: license_tr.txt
;Name: fa; MessagesFile: "compiler:Languages\Farsi.isl"; InfoBeforeFile: license_fa.txt
;Name: sv; MessagesFile: "compiler:Languages\Swedish.isl"; InfoBeforeFile: license_sv.txt

[CustomMessages]
en.sendReport=Send a reports to author's web-site if any error occurred
ru.sendReport=Посылать отчет разработчику при возникновении ошибки
uk.sendReport=Відправляти звіт автору при виникненні помилки
es.sendReport=Escribir un mensaje al autor del sitio web si ocurre algún error
fr.sendReport=Envoyer un rapport a l'auteur du site-web si une erreur se produit
hu.sendReport=Hiba elkuldese a keszitonek
pt.sendReport=Enviar um relatorio para o site do autor se ocorrer um erro
de.sendReport=Send a reports to author's web-site if any error occurred
;el.sendReport=Αποστολή αναφορών στον ιστότοπο του συγγραφέα σε περίπτωση σφάλματος
cs.sendReport=Send a reports to author's web-site if any error occurred
it.sendReport=Invia un rapporto al sito web dell'autore se e avvenuto un errore
pl.sendReport=Wyslij raport do Autorow w przypadku problemow
ca.sendReport=Envieu un informe a la pagina web de l'autor si hi ha cap error
nl.sendReport=Stuur een rapport naar de auteur als er een fout is opgetreden
bg.sendReport=Изпращане на отчети до уеб сайта на автора, ако възникне някаква грешка
;lv.sendReport=Nosūtīt ziņojumu uz autora tīmekļvietni, ja radusies kāda kļūda
tr.sendReport=Herhangi bir hata durumunda geliştirici web sitesine rapor gönder
;fa.sendReport=Send a reports to author's web-site if any error occurred
;sv.sendReport=Skicka rapporter till Utvecklarens webbplats om något fel inträffade

en.checkUpdate=Automatically check for updates
ru.checkUpdate=Проверять обновления автоматически
uk.checkUpdate=Перевіряти оновлення автоматично
es.checkUpdate=Comprobar actualizaciones automáticamente
fr.checkUpdate=Verification automatique des mises a jour
hu.checkUpdate=Automatically check for updates
pt.checkUpdate=Procurar atualizacoes automaticamente
de.checkUpdate=Automatically check for updates
;el.checkUpdate=Αυτόματος έλεγχος για ενημερώσεις
cs.checkUpdate=Automatically check for updates
it.checkUpdate=Cerca automaticamente gli aggiornamenti
pl.checkUpdate=Automatycznie sprawdzaj w poszukiwaniu najnowszej wersji
ca.checkUpdate=Comprova si hi ha actualitzacions automaticament
nl.checkUpdate=Automatisch controleren op update's
bg.checkUpdate=Автоматична проверка за актуализации
;lv.checkUpdate=Automātiski meklēt atjauninājumus
tr.checkUpdate=Güncellemeleri otomatik olarak kontrol et
;fa.checkUpdate=به صورت خودکار به‌روزرسانی‌ها بررسی شود
;sv.checkUpdate=Sök efter uppdateringar

en.associate=Associate *.db files with OpenNumismat
ru.associate=Связать *.db файлы с OpenNumismat
uk.associate=Ассоціювати файли *.db з OpenNumismat
es.associate=Asociar archivos *.db con OpenNumismat
fr.associate=Associer les fichiers *.db avec OpenNumismat
hu.associate=Associate *.db files with OpenNumismat
pt.associate=Associar ficheiros *.db com o OpenNumismat
de.associate=Associate *.db files with OpenNumismat
;el.associate=Συσχέτιση αρχείων *.db με το OpenNumismat
cs.associate=Associate *.db files with OpenNumismat
it.associate=Associare i file *.db con OpenNumismat
pl.associate=Skojarz rozszerzenie *.db z OpenNumismat
ca.associate=Associa fitxers *.db amb OpenNumismat
nl.associate=Associate *.db files with OpenNumismat
bg.associate=Асоциирай *.db файлове с OpenNumismat
;lv.associate=Saistīt *.db failus ar OpenNumismat
tr.associate=*.db dosyalarını OpenNumismat'la ilişkilendir
;fa.associate=Associate *.db files with OpenNumismat
;sv.associate=Associera *.db-filer med OpenNumismat

[Files]
Source: "..\open-numismat.dist\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "..\open-numismat.dist\db\demo_en.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: en; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\demo_ru.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: ru; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\demo_uk.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: uk; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\demo_es.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: es; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\demo_fr.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: fr; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\demo_hu.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: hu; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\demo_pt.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: pt; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\demo_de.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: de; Flags: onlyifdoesntexist
;Source: "..\open-numismat.dist\db\demo_el.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: el; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\demo_cs.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: cs; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\demo_it.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: it; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\demo_pl.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: pl; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\demo_ca.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: ca; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\demo_nl.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: nl; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\demo_bg.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: bg; Flags: onlyifdoesntexist
;Source: "..\open-numismat.dist\db\demo_lv.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: lv; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\demo_tr.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: tr; Flags: onlyifdoesntexist
;Source: "..\open-numismat.dist\db\demo_fa.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: fa; Flags: onlyifdoesntexist
;Source: "..\open-numismat.dist\db\demo_sv.db"; DestDir: "{userdocs}\OpenNumismat"; DestName: "MyCollection.db"; Languages: sv; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\reference_en.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: en; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\reference_ru.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: ru; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\reference_uk.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: uk; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\reference_es.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: es; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\reference_fr.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: fr; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\reference_hu.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: hu; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\reference_pt.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: pt; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\reference_de.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: de; Flags: onlyifdoesntexist
;Source: "..\open-numismat.dist\db\reference_el.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: el; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\reference_cs.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: cs; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\reference_it.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: it; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\reference_pl.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: pl; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\reference_ca.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: ca; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\reference_nl.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: nl; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\reference_bg.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: bg; Flags: onlyifdoesntexist
;Source: "..\open-numismat.dist\db\reference_lv.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: lv; Flags: onlyifdoesntexist
Source: "..\open-numismat.dist\db\reference_tr.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: tr; Flags: onlyifdoesntexist
;Source: "..\open-numismat.dist\db\reference_fa.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: fa; Flags: onlyifdoesntexist
;Source: "..\open-numismat.dist\db\reference_sv.ref"; DestDir: "{userdocs}\OpenNumismat"; DestName: "reference.ref"; Languages: sv; Flags: onlyifdoesntexist

[Dirs]
Name: "{userdocs}\OpenNumismat"
Name: "{userdocs}\OpenNumismat\backup"
Name: "{userdocs}\OpenNumismat\templates"

[Registry]
Root: HKCU; Subkey: "Software\Janis"; Flags: uninsdeletekeyifempty
Root: HKCU; Subkey: "Software\Janis\OpenNumismat"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Janis\OpenNumismat\mainwindow"; ValueType: string; ValueName: "error"; ValueData: "true"; Tasks: sendreport
Root: HKCU; Subkey: "Software\Janis\OpenNumismat\mainwindow"; ValueType: string; ValueName: "updates"; ValueData: "true"; Tasks: checkupdate
Root: HKCR; Subkey: ".db"; ValueType: string; ValueName: ""; ValueData: "OpenNumismatCollection"; Flags: uninsdeletevalue; Tasks: associate 
Root: HKCR; Subkey: "OpenNumismatCollection"; ValueType: string; ValueName: ""; ValueData: "OpenNumismat collection"; Flags: uninsdeletekey; Tasks: associate
Root: HKCR; Subkey: "OpenNumismatCollection\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\OpenNumismat.EXE,0"; Flags: uninsdeletekey; Tasks: associate
Root: HKCR; Subkey: "OpenNumismatCollection\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\OpenNumismat.EXE"" ""%1"""; Flags: uninsdeletekey; Tasks: associate

[Icons]
Name: "{group}\OpenNumismat"; Filename: "{app}\OpenNumismat.exe"
Name: "{group}\Uninstall OpenNumismat"; Filename: "{uninstallexe}"
Name: "{userdesktop}\OpenNumismat"; Filename: "{app}\OpenNumismat.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\OpenNumismat"; Filename: "{app}\OpenNumismat.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\OpenNumismat.exe"; Flags: postinstall nowait skipifsilent

[Tasks]
Name: associate; Description: "{cm:associate}"; Flags: unchecked
Name: sendreport; Description: "{cm:sendReport}"
Name: checkupdate; Description: "{cm:checkUpdate}"
Name: desktopicon; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: quicklaunchicon; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[UninstallDelete]
Type: filesandordirs; Name: {localappdata}\Janis\OpenNumismat;

[InstallDelete]
Type: filesandordirs; Name: {app}\Pythonwin;
Type: filesandordirs; Name: {app}\pywin32_system32;
Type: filesandordirs; Name: {app}\win32;
Type: filesandordirs; Name: {app}\win32com;
Type: filesandordirs; Name: {app}\PySide6\plugins;
Type: filesandordirs; Name: {app}\PySide6\resources;
Type: files; Name: {app}\base_library.zip;
Type: files; Name: {app}\ucrtbase.dll;
Type: files; Name: {app}\api-ms-win-*-0.dll;
Type: files; Name: {app}\PySide6\*.dll;
Type: files; Name: {app}\PySide6\*.exe;
Type: files; Name: {app}\shiboken6\shiboken6.abi3.dll;
