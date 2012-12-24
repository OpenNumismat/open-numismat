from PyQt4 import QtCore, QtGui, QtWebKit
from PyQt4.QtCore import Qt

from Tools import TemporaryDir
from Reports import Report
from Settings import Settings


class QPrintPreviewMainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(QPrintPreviewMainWindow, self).__init__(parent)

    def createPopupMenu(self):
        return None


class PreviewDialog(QtGui.QDialog):
    def __init__(self, model, records, parent=None):
        super(PreviewDialog, self).__init__(parent,
                        Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint)

        self.records = records
        self.model = model

        self.webView = QtWebKit.QWebView(self)
        self.webView.setVisible(False)
        self.webView.loadFinished.connect(self._loadFinished)

        self.preview = QtGui.QPrintPreviewWidget(self)

        self.preview.paintRequested.connect(self.paintRequested)
        self.preview.previewChanged.connect(self.previewChanged)
        self.setupActions()

        self.templateSelector = QtGui.QComboBox(self)
        self.templateSelector.currentIndexChanged.connect(self._templateChanged)
        for i, template in enumerate(Report.scanTemplates()):
            self.templateSelector.addItem(template)
            if Settings()['template'] == template:
                current = i
        self.templateSelector.setCurrentIndex(current)

        mw = QPrintPreviewMainWindow(self)
        toolbar = QtGui.QToolBar(mw)

        toolbar.addWidget(self.templateSelector)
        toolbar.addSeparator()
        toolbar.addAction(self.fitWidthAction)
        toolbar.addAction(self.fitPageAction)
        toolbar.addSeparator()
        toolbar.addAction(self.portraitAction)
        toolbar.addAction(self.landscapeAction)
        toolbar.addSeparator()
        toolbar.addAction(self.singleModeAction)
        toolbar.addAction(self.facingModeAction)
        toolbar.addAction(self.overviewModeAction)

        mw.addToolBar(toolbar)
        mw.setCentralWidget(self.preview)
        mw.setParent(self, Qt.Widget)

        topLayout = QtGui.QVBoxLayout()
        topLayout.addWidget(mw)
        topLayout.setMargin(0)
        self.setLayout(topLayout)

        self.preview.setFocus()

    def setupActions(self):
        self.fitGroup = QtGui.QActionGroup(self)
        self.fitWidthAction = self.fitGroup.addAction(QtGui.QApplication.translate("QPrintPreviewDialog", "Fit width"))
        self.fitPageAction = self.fitGroup.addAction(QtGui.QApplication.translate("QPrintPreviewDialog", "Fit page"))
        self.fitWidthAction.setCheckable(True)
        self.fitPageAction.setCheckable(True)
        self.qt_setupActionIcon(self.fitWidthAction, "fit-width")
        self.qt_setupActionIcon(self.fitPageAction, "fit-page")

        # Portrait/Landscape
        self.orientationGroup = QtGui.QActionGroup(self)
        self.portraitAction = self.orientationGroup.addAction(QtGui.QApplication.translate("QPrintPreviewDialog", "Portrait"))
        self.landscapeAction = self.orientationGroup.addAction(QtGui.QApplication.translate("QPrintPreviewDialog", "Landscape"))
        self.portraitAction.setCheckable(True)
        self.landscapeAction.setCheckable(True)
        self.qt_setupActionIcon(self.portraitAction, "layout-portrait")
        self.qt_setupActionIcon(self.landscapeAction, "layout-landscape")

        # Display mode
        self.modeGroup = QtGui.QActionGroup(self)
        self.singleModeAction = self.modeGroup.addAction(QtGui.QApplication.translate("QPrintPreviewDialog", "Show single page"))
        self.facingModeAction = self.modeGroup.addAction(QtGui.QApplication.translate("QPrintPreviewDialog", "Show facing pages"))
        self.overviewModeAction = self.modeGroup.addAction(QtGui.QApplication.translate("QPrintPreviewDialog", "Show overview of all pages"))
        self.singleModeAction.setCheckable(True)
        self.facingModeAction.setCheckable(True)
        self.overviewModeAction.setCheckable(True)
        self.qt_setupActionIcon(self.singleModeAction, "view-page-one")
        self.qt_setupActionIcon(self.facingModeAction, "view-page-sided")
        self.qt_setupActionIcon(self.overviewModeAction, "view-page-multi")

        # Initial state:
        self.fitWidthAction.setChecked(True)
        self.singleModeAction.setChecked(True)
        if self.preview.orientation() == QtGui.QPrinter.Portrait:
            self.portraitAction.setChecked(True)
        else:
            self.landscapeAction.setChecked(True)

    def paintRequested(self, printer):
        self.webView.print_(printer)

    def previewChanged(self):
        pass

    def qt_setupActionIcon(self, action, name):
        imagePrefix = ":/trolltech/dialogs/qprintpreviewdialog/images/"
        icon = QtGui.QIcon()
        icon.addFile(imagePrefix + name + "-24.png", QtCore.QSize(24, 24))
        icon.addFile(imagePrefix + name + "-32.png", QtCore.QSize(32, 32))
        action.setIcon(icon)

    def _loadFinished(self, ok):
        self.preview.updatePreview()

    def _templateChanged(self, index):
        template_name = self.templateSelector.currentText()
        report = Report.Report(self.model, TemporaryDir.path())
        fileName = report.generate(template_name, self.records, True)
        if not fileName:
            return  #TODO: !!!

        file = QtCore.QFile(fileName)
        file.open(QtCore.QIODevice.ReadOnly)

        out = QtCore.QTextStream(file)
        out.setCodec(QtCore.QTextCodec.codecForName('utf-8'))
        html = out.readAll()

        basePath = QtCore.QFileInfo(fileName).absolutePath()

        baseUrl = QtCore.QUrl.fromLocalFile(basePath + '/')
        self.webView.setHtml(html, baseUrl)
