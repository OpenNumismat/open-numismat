import os.path

from PySide6.QtCore import QMarginsF, QSize, QUrl
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPageSetupDialog
from PySide6.QtWebEngineCore import  QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView

import OpenNumismat
from OpenNumismat.Tools import TemporaryDir
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Reports import Report
from OpenNumismat.Settings import Settings
from OpenNumismat.Tools.Gui import getSaveFileName, infoMessageBox
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator

exportToWordAvailable = True
try:
    import win32com.client
except ImportError:
    print('win32com module missed. Exporting to Word not available')
    exportToWordAvailable = False


class WebEnginePage(QWebEnginePage):
    def acceptNavigationRequest(self, url, type_, isMainFrame):
        if type_ == QWebEnginePage.NavigationTypeLinkClicked:
            return False
        return super().acceptNavigationRequest(url, type_, isMainFrame)
    

class QWebView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPage(WebEnginePage(self))
    
    def contextMenuEvent(self, _event):
        pass


@storeDlgSizeDecorator
class PreviewDialog(QDialog):

    def __init__(self, model, indexes, parent=None):
        super().__init__(parent, Qt.WindowSystemMenuHint |
                         Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)

        self.started = False

        self.indexes = indexes
        self.model = model

        self.webView = QWebView(self)
        self.webView.setVisible(True)
        self.webView.loadFinished.connect(self._loadFinished)

        self.printer = QPrinter(QPrinter.HighResolution)
        self.printer.setPageMargins(QMarginsF(12.7, 10, 10, 10))

        self.setupActions()

        self.templateSelector = QComboBox(self)
        current = 0
        for i, template in enumerate(Report.scanTemplates()):
            self.templateSelector.addItem(template[0], template[1])
            if Settings()['template'] == template[1]:
                current = i
        self.templateSelector.setCurrentIndex(-1)
        self.templateSelector.currentIndexChanged.connect(self._templateChanged)

        toolbar = QToolBar()

        toolbar.addWidget(self.templateSelector)
        toolbar.addSeparator()
        toolbar.addAction(self.printAction)
        toolbar.addAction(self.htmlAction)
        toolbar.addAction(self.pdfAction)
        if exportToWordAvailable:
            toolbar.addAction(self.wordAction)

        toolbar.addSeparator()
        toolbar.addAction(self.pageSetupAction)

        topLayout = QVBoxLayout()
        topLayout.addWidget(toolbar)
        topLayout.addWidget(self.webView)
        topLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(topLayout)

        self.setWindowTitle(self.tr("Report preview"))

        self.webView.setFocus()

        self.templateSelector.setCurrentIndex(current)

    def setupActions(self):
        # Print
        self.printerGroup = QActionGroup(self)
        self.printAction = self.printerGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Print"))
        self.qt_setupActionIcon(self.printAction, "printer")
        self.printAction.triggered.connect(self._q_print)
        self.pageSetupAction = self.printerGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Page setup"))
        self.qt_setupActionIcon(self.pageSetupAction, "page-setup")
        self.pageSetupAction.triggered.connect(self._q_pageSetup)

        # Export
        self.exportGroup = QActionGroup(self)
        if exportToWordAvailable:
            self.wordAction = self.exportGroup.addAction(
                            QIcon(':/Document_Microsoft_Word.png'),
                            self.tr("Save as MS Word document"))
        self.htmlAction = self.exportGroup.addAction(
                        QIcon(':/Web_HTML.png'),
                        self.tr("Save as HTML files"))
        self.pdfAction = self.exportGroup.addAction(
                        QIcon(':/Adobe_PDF_Document.png'),
                        self.tr("Save as PDF file"))
        self.exportGroup.triggered.connect(self._q_export)

    def qt_setupActionIcon(self, action, name):
        imagePrefix = ":/qt-project.org/dialogs/qprintpreviewdialog/images/"
        icon = QIcon()
        icon.addFile(imagePrefix + name + "-24.png", QSize(24, 24))
        icon.addFile(imagePrefix + name + "-32.png", QSize(32, 32))
        action.setIcon(icon)

    @waitCursorDecorator
    def _loadFinished(self, _ok):
        if not self.started:
            # Fist rendering is done - show dialog
            self.started = True
            self.setVisible(True)

    def _templateChanged(self, _index):
        template_name = self.templateSelector.currentText()
        template = self.templateSelector.currentData()
        dstPath = os.path.join(TemporaryDir.path(), template_name + '.htm')
        report = Report.Report(self.model, template, dstPath, self.parent())
        self.fileName = report.generate(self.indexes, True)
        if not self.fileName:
            return

        self.webView.load(QUrl.fromLocalFile(self.fileName))

    def _q_print(self):
        printDialog = QPrintDialog(self.printer, self)
        if printDialog.exec_() == QDialog.Accepted:
            self.webView.print(self.printer)

            self.accept()

    def _q_pageSetup(self):
        QPageSetupDialog(self.printer, self).exec()

    def _q_export(self, action):
        if exportToWordAvailable and action == self.wordAction:
            fileName, _selectedFilter = getSaveFileName(
                self, 'export', '',
                OpenNumismat.HOME_PATH, self.tr("Word documents (*.doc)"))
            if fileName:
                self.__exportToWord(self.fileName, fileName)
        elif action == self.htmlAction:
            fileName, _selectedFilter = getSaveFileName(
                self, 'export', '',
                OpenNumismat.HOME_PATH, self.tr("Web page (*.htm *.html)"))
            if fileName:
                self.__exportToHtml(fileName)
        elif action == self.pdfAction:
            fileName, _selectedFilter = getSaveFileName(
                self, 'export', '',
                OpenNumismat.HOME_PATH, self.tr("PDF file (*.pdf)"))
            if fileName:
                self.__exportToPdf(fileName)

    @waitCursorDecorator
    def __exportToWord(self, src, dst):
        word = win32com.client.DispatchEx('Word.Application')

        doc = word.Documents.Add(src)
        doc.SaveAs(dst, FileFormat=0)
        doc.Close()

        word.Quit()

    @waitCursorDecorator
    def __exportToHtml(self, fileName):
        template = self.templateSelector.currentData()
        report = Report.Report(self.model, template, fileName)
        self.fileName = report.generate(self.indexes, True)

    def __exportToPdf(self, fileName):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        
        pageParams = self.printer.pageLayout()
        if pageParams.pageSize().id() == QPageSize.Custom:
            pageParams = QPageLayout()

        self.webView.page().pdfPrintingFinished.connect(self.pdfPrintingFinished)
        self.webView.page().printToPdf(fileName, pageParams)
    
    def pdfPrintingFinished(self, file_path, success):
        self.webView.page().pdfPrintingFinished.disconnect(self.pdfPrintingFinished)
        QApplication.restoreOverrideCursor()

        if success:
            infoMessageBox("pdfPrintingFinished", self.tr("Report saving"),
                           self.tr("Report saved as %s") % file_path,
                           parent=self)
        else:
            QMessageBox.critical(self, self.tr("Report saving"),
                                 self.tr("Report saving failed"))
