from PyQt4.QtGui import QDesktopServices

Company = 'Janis'
AppName = 'OpenNumismat'
Version = '1.3.1'
Web = 'http://code.google.com/p/open-numismat/'
__docDir = QDesktopServices.storageLocation(QDesktopServices.DocumentsLocation)
AppDir = "%s/%s" % (__docDir, AppName)
