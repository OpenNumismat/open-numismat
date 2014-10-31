import os.path

exportToWordAvailable = True

try:
    import win32com.client
except ImportError:
    print('win32com module missed. Exporting to Word not available')
    exportToWordAvailable = False

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewWidget, QPrintDialog, QPageSetupDialog
from PyQt5.QtWebKitWidgets import QWebView

from OpenNumismat.Tools import TemporaryDir
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Reports import Report
from OpenNumismat.Settings import Settings
from OpenNumismat.Tools.Gui import createIcon
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator


class QPrintPreviewMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(QPrintPreviewMainWindow, self).__init__(parent)

    def createPopupMenu(self):
        return None


class ZoomFactorValidator(QDoubleValidator):
    def __init__(self, bottom, top, decimals, parent):
        super(ZoomFactorValidator, self).__init__(bottom, top, decimals, parent)

    def validate(self, input, pos):
        replacePercent = False
        if len(input) and input[-1] == '%':
            input = input[:-1]
            replacePercent = True
        state, _1, _2 = super(ZoomFactorValidator, self).validate(input, pos)
        if replacePercent:
            input += '%'
        num_size = 4
        if state == QDoubleValidator.Intermediate:
            i = input.find(QtCore.QLocale.system().decimalPoint())
            if (i == -1 and len(input) > num_size) \
                    or (i != -1 and i > num_size):
                return QDoubleValidator.Invalid, input, pos

        return state, input, pos


class LineEdit(QLineEdit):
    def __init__(self, parent=None):
        super(LineEdit, self).__init__(parent)

        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.returnPressed.connect(self.handleReturnPressed)

        self.origText = ''

    def focusInEvent(self, e):
        self.origText = self.text()
        super(LineEdit, self).focusInEvent(e)

    def focusOutEvent(self, e):
        if self.isModified() and not self.hasAcceptableInput():
            self.setText(self.origText)
        super(LineEdit, self).focusOutEvent(e)

    def handleReturnPressed(self):
        self.origText = self.text()


@storeDlgSizeDecorator
class PreviewDialog(QDialog):
    def __init__(self, model, records, parent=None):
        super().__init__(parent, Qt.WindowSystemMenuHint |
                         Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)

        self.started = False

        self.records = records
        self.model = model

        self.webView = QWebView(self)
        self.webView.setVisible(False)
        self.webView.loadFinished.connect(self._loadFinished)

        self.printer = QPrinter()
        self.printer.setPageMargins(12.7, 10, 10, 10, QPrinter.Millimeter)
        self.preview = QPrintPreviewWidget(self.printer, self)

        self.preview.paintRequested.connect(self.paintRequested)
        self.preview.previewChanged.connect(self._q_previewChanged)
        self.setupActions()

        self.templateSelector = QComboBox(self)
        current = 0
        for i, template in enumerate(Report.scanTemplates()):
            self.templateSelector.addItem(template)
            if Settings()['template'] == template:
                current = i
        self.templateSelector.setCurrentIndex(-1)
        self.templateSelector.currentIndexChanged.connect(self._templateChanged)

        self.pageNumEdit = LineEdit()
        self.pageNumEdit.setAlignment(Qt.AlignRight)
        self.pageNumEdit.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.pageNumLabel = QLabel()
        self.pageNumEdit.editingFinished.connect(self._q_pageNumEdited)

        self.zoomFactor = QComboBox()
        self.zoomFactor.setEditable(True)
        self.zoomFactor.setMinimumContentsLength(7)
        self.zoomFactor.setInsertPolicy(QComboBox.NoInsert)
        zoomEditor = LineEdit()
        zoomEditor.setValidator(ZoomFactorValidator(1, 1000, 1, zoomEditor))
        self.zoomFactor.setLineEdit(zoomEditor)
        factorsX2 = [25, 50, 100, 200, 250, 300, 400, 800, 1600]
        for factor in factorsX2:
            self.zoomFactor.addItem("%g%%" % (factor / 2.0))
        self.zoomFactor.lineEdit().editingFinished.connect(self._q_zoomFactorChanged)
        self.zoomFactor.currentIndexChanged.connect(self._q_zoomFactorChanged)

        mw = QPrintPreviewMainWindow(self)
        toolbar = QToolBar(mw)

        toolbar.addWidget(self.templateSelector)
        toolbar.addSeparator()
        toolbar.addAction(self.printAction)
        toolbar.addAction(self.htmlAction)
        toolbar.addAction(self.pdfAction)
        if exportToWordAvailable:
            toolbar.addAction(self.wordAction)
        toolbar.addSeparator()
        toolbar.addAction(self.fitWidthAction)
        toolbar.addAction(self.fitPageAction)
        toolbar.addSeparator()
        toolbar.addWidget(self.zoomFactor)
        toolbar.addAction(self.zoomOutAction)
        toolbar.addAction(self.zoomInAction)
        toolbar.addSeparator()
        toolbar.addAction(self.portraitAction)
        toolbar.addAction(self.landscapeAction)
        toolbar.addSeparator()
        toolbar.addAction(self.firstPageAction)
        toolbar.addAction(self.prevPageAction)

        pageEdit = QWidget(toolbar)
        vboxLayout = QVBoxLayout()
        vboxLayout.setContentsMargins(0, 0, 0, 0)
        formLayout = QFormLayout()
        formLayout.setWidget(0, QFormLayout.LabelRole, self.pageNumEdit)
        formLayout.setWidget(0, QFormLayout.FieldRole, self.pageNumLabel)
        vboxLayout.addLayout(formLayout)
        vboxLayout.setAlignment(Qt.AlignVCenter)
        pageEdit.setLayout(vboxLayout)
        toolbar.addWidget(pageEdit)

        toolbar.addAction(self.nextPageAction)
        toolbar.addAction(self.lastPageAction)
        toolbar.addSeparator()
        toolbar.addAction(self.singleModeAction)
        toolbar.addAction(self.facingModeAction)
        toolbar.addAction(self.overviewModeAction)
        toolbar.addSeparator()
        toolbar.addAction(self.pageSetupAction)

        # Cannot use the actions' triggered signal here, since it doesn't autorepeat
        zoomInButton = toolbar.widgetForAction(self.zoomInAction)
        zoomOutButton = toolbar.widgetForAction(self.zoomOutAction)
        zoomInButton.setAutoRepeat(True)
        zoomInButton.setAutoRepeatInterval(200)
        zoomInButton.setAutoRepeatDelay(200)
        zoomOutButton.setAutoRepeat(True)
        zoomOutButton.setAutoRepeatInterval(200)
        zoomOutButton.setAutoRepeatDelay(200)
        zoomInButton.clicked.connect(self._q_zoomIn)
        zoomOutButton.clicked.connect(self._q_zoomOut)

        mw.addToolBar(toolbar)
        mw.setCentralWidget(self.preview)
        mw.setParent(self, Qt.Widget)

        topLayout = QVBoxLayout()
        topLayout.addWidget(mw)
        topLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(topLayout)

        self.setWindowTitle(self.tr("Report preview"))

        self.preview.setFocus()

        self.templateSelector.setCurrentIndex(current)

    def setupActions(self):
        # Navigation
        self.navGroup = QActionGroup(self)
        self.navGroup.setExclusive(False)
        self.nextPageAction = self.navGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Next page"))
        self.prevPageAction = self.navGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Previous page"))
        self.firstPageAction = self.navGroup.addAction(QApplication.translate("QPrintPreviewDialog", "First page"))
        self.lastPageAction = self.navGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Last page"))
        self.qt_setupActionIcon(self.nextPageAction, "go-next")
        self.qt_setupActionIcon(self.prevPageAction, "go-previous")
        self.qt_setupActionIcon(self.firstPageAction, "go-first")
        self.qt_setupActionIcon(self.lastPageAction, "go-last")
        self.navGroup.triggered.connect(self._q_navigate)

        self.fitGroup = QActionGroup(self)
        self.fitWidthAction = self.fitGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Fit width"))
        self.fitPageAction = self.fitGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Fit page"))
        self.fitWidthAction.setCheckable(True)
        self.fitPageAction.setCheckable(True)
        self.qt_setupActionIcon(self.fitWidthAction, "fit-width")
        self.qt_setupActionIcon(self.fitPageAction, "fit-page")
        self.fitGroup.triggered.connect(self._q_fit)

        # Zoom
        self.zoomGroup = QActionGroup(self)
        self.zoomInAction = self.zoomGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Zoom in"))
        self.zoomOutAction = self.zoomGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Zoom out"))
        self.qt_setupActionIcon(self.zoomInAction, "zoom-in")
        self.qt_setupActionIcon(self.zoomOutAction, "zoom-out")

        # Portrait/Landscape
        self.orientationGroup = QActionGroup(self)
        self.portraitAction = self.orientationGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Portrait"))
        self.landscapeAction = self.orientationGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Landscape"))
        self.portraitAction.setCheckable(True)
        self.landscapeAction.setCheckable(True)
        self.qt_setupActionIcon(self.portraitAction, "layout-portrait")
        self.qt_setupActionIcon(self.landscapeAction, "layout-landscape")
        self.portraitAction.triggered.connect(self.preview.setPortraitOrientation)
        self.landscapeAction.triggered.connect(self.preview.setLandscapeOrientation)

        # Display mode
        self.modeGroup = QActionGroup(self)
        self.singleModeAction = self.modeGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Show single page"))
        self.facingModeAction = self.modeGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Show facing pages"))
        self.overviewModeAction = self.modeGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Show overview of all pages"))
        self.singleModeAction.setCheckable(True)
        self.facingModeAction.setCheckable(True)
        self.overviewModeAction.setCheckable(True)
        self.qt_setupActionIcon(self.singleModeAction, "view-page-one")
        self.qt_setupActionIcon(self.facingModeAction, "view-page-sided")
        self.qt_setupActionIcon(self.overviewModeAction, "view-page-multi")
        self.modeGroup.triggered.connect(self._q_setMode)

        # Print
        self.printerGroup = QActionGroup(self)
        self.printAction = self.printerGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Print"))
        self.pageSetupAction = self.printerGroup.addAction(QApplication.translate("QPrintPreviewDialog", "Page setup"))
        self.qt_setupActionIcon(self.printAction, "print")
        self.qt_setupActionIcon(self.pageSetupAction, "page-setup")
        self.printAction.triggered.connect(self._q_print)
        self.pageSetupAction.triggered.connect(self._q_pageSetup)
        # Export
        self.exportGroup = QActionGroup(self)
        if exportToWordAvailable:
            self.wordAction = self.exportGroup.addAction(
                            createIcon('Document_Microsoft_Word.png'),
                            self.tr("Save as MS Word document"))
        self.htmlAction = self.exportGroup.addAction(
                        createIcon('Web_HTML.png'),
                        self.tr("Save as HTML files"))
        self.pdfAction = self.exportGroup.addAction(
                        createIcon('Adobe_PDF_Document.png'),
                        self.tr("Save as PDF file"))
        self.exportGroup.triggered.connect(self._q_export)

        # Initial state:
        self.fitPageAction.setChecked(True)
        self.singleModeAction.setChecked(True)
        if self.preview.orientation() == QPrinter.Portrait:
            self.portraitAction.setChecked(True)
        else:
            self.landscapeAction.setChecked(True)

    def exec_(self):
        pass

    def paintRequested(self, printer):
        self.webView.print_(printer)

    def qt_setupActionIcon(self, action, name):
        imagePrefix = ":/qt-project.org/dialogs/qprintpreviewdialog/images/"
        icon = QIcon()
        icon.addFile(imagePrefix + name + "-24.png", QtCore.QSize(24, 24))
        icon.addFile(imagePrefix + name + "-32.png", QtCore.QSize(32, 32))
        action.setIcon(icon)

    def _loadFinished(self, ok):
        self.preview.updatePreview()
        if not self.started:
            # Fist rendering is done - show dialog
            self.started = True
            self.setVisible(True)

    def _templateChanged(self, index):
        template_name = self.templateSelector.currentText()
        dstPath = os.path.join(TemporaryDir.path(), template_name + '.htm')
        report = Report.Report(self.model, template_name, dstPath)
        self.fileName = report.generate(self.records, True)
        if not self.fileName:
            return

        file = QtCore.QFile(self.fileName)
        file.open(QtCore.QIODevice.ReadOnly)

        out = QtCore.QTextStream(file)
        out.setCodec(QtCore.QTextCodec.codecForName('utf-8'))
        html = out.readAll()

        basePath = QtCore.QFileInfo(self.fileName).absolutePath()

        baseUrl = QtCore.QUrl.fromLocalFile(basePath + '/')
        self.webView.setHtml(html, baseUrl)

    def isFitting(self):
        return (self.fitGroup.isExclusive() \
            and (self.fitWidthAction.isChecked() or self.fitPageAction.isChecked()))

    def setFitting(self, on):
        if self.isFitting() == on:
            return
        self.fitGroup.setExclusive(on)
        if on:
            if self.fitWidthAction.isChecked():
                action = self.fitWidthAction
            else:
                action = self.fitPageAction
            action.setChecked(True)
            if self.fitGroup.checkedAction() != action:
                # work around exclusitivity problem
                self.fitGroup.removeAction(action)
                self.fitGroup.addAction(action)
        else:
            self.fitWidthAction.setChecked(False)
            self.fitPageAction.setChecked(False)

    def updateNavActions(self):
        curPage = self.preview.currentPage()
        numPages = self.preview.pageCount()
        self.nextPageAction.setEnabled(curPage < numPages)
        self.prevPageAction.setEnabled(curPage > 1)
        self.firstPageAction.setEnabled(curPage > 1)
        self.lastPageAction.setEnabled(curPage < numPages)
        self.pageNumEdit.setText(str(curPage))

    def updatePageNumLabel(self):
        numPages = self.preview.pageCount()
        maxChars = len(str(numPages))
        self.pageNumLabel.setText("/ %d" % numPages)
        cyphersWidth = self.fontMetrics().width('8' * maxChars)
        maxWidth = self.pageNumEdit.minimumSizeHint().width() + cyphersWidth
        self.pageNumEdit.setMinimumWidth(maxWidth)
        self.pageNumEdit.setMaximumWidth(maxWidth)
        self.pageNumEdit.setValidator(QIntValidator(1, numPages, self.pageNumEdit))

    def updateZoomFactor(self):
        self.zoomFactor.lineEdit().setText("%.1f%%" % (self.preview.zoomFactor() * 100))

    def _q_fit(self, action):
        self.setFitting(True)
        if action == self.fitPageAction:
            self.preview.fitInView()
        else:
            self.preview.fitToWidth()

    def _q_zoomIn(self):
        self.setFitting(False)
        self.preview.zoomIn()
        self.updateZoomFactor()

    def _q_zoomOut(self):
        self.setFitting(False)
        self.preview.zoomOut()
        self.updateZoomFactor()

    def _q_pageNumEdited(self):
        try:
            res = int(self.pageNumEdit.text())
            self.preview.setCurrentPage(res)
        except ValueError:
            pass

    def _q_navigate(self, action):
        curPage = self.preview.currentPage()
        if action == self.prevPageAction:
            self.preview.setCurrentPage(curPage - 1)
        elif action == self.nextPageAction:
            self.preview.setCurrentPage(curPage + 1)
        elif action == self.firstPageAction:
            self.preview.setCurrentPage(1)
        elif action == self.lastPageAction:
            self.preview.setCurrentPage(self.preview.pageCount())
        self.updateNavActions()

    def _q_setMode(self, action):
        if action == self.overviewModeAction:
            self.preview.setViewMode(QPrintPreviewWidget.AllPagesView)
            self.setFitting(False)
            self.fitGroup.setEnabled(False)
            self.navGroup.setEnabled(False)
            self.pageNumEdit.setEnabled(False)
            self.pageNumLabel.setEnabled(False)
        elif action == self.facingModeAction:
            self.preview.setViewMode(QPrintPreviewWidget.FacingPagesView)
        else:
            self.preview.setViewMode(QPrintPreviewWidget.SinglePageView)

        if action == self.facingModeAction or action == self.singleModeAction:
            self.fitGroup.setEnabled(True)
            self.navGroup.setEnabled(True)
            self.pageNumEdit.setEnabled(True)
            self.pageNumLabel.setEnabled(True)
            self.setFitting(True)

    def _q_print(self):
        printDialog = QPrintDialog(self.printer, self)
        if printDialog.exec_() == QDialog.Accepted:
            self.preview.print_()
            self.accept()

    def _q_pageSetup(self):
        pageSetup = QPageSetupDialog(self.printer, self)
        if pageSetup.exec_() == QDialog.Accepted:
            # update possible orientation changes
            if self.preview.orientation() == QPrinter.Portrait:
                self.portraitAction.setChecked(True)
                self.preview.setPortraitOrientation()
            else:
                self.landscapeAction.setChecked(True)
                self.preview.setLandscapeOrientation()

    def _q_export(self, action):
        settings = QtCore.QSettings()
        lastExportDir = settings.value('export/last_dir') or ''

        if exportToWordAvailable and action == self.wordAction:
            fileName, _selectedFilter = QFileDialog.getSaveFileName(self,
                                self.tr("Save as"), lastExportDir,
                                filter=self.tr("Word documents (*.doc)"))
            if fileName:
                self.__exportToWord(self.fileName, fileName)
        elif action == self.htmlAction:
            fileName, _selectedFilter = QFileDialog.getSaveFileName(self,
                                self.tr("Save as"), lastExportDir,
                                filter=self.tr("Web page (*.htm *.html)"))
            if fileName:
                self.__exportToHtml(fileName)
        elif action == self.pdfAction:
            fileName, _selectedFilter = QFileDialog.getSaveFileName(self,
                                self.tr("Save as"), lastExportDir,
                                filter=self.tr("PDF file (*.pdf)"))
            if fileName:
                self.__exportToPdf(fileName)

        if fileName:
            file_info = QtCore.QFileInfo(fileName)
            settings.setValue('export/last_dir', file_info.absolutePath())

    @waitCursorDecorator
    def __exportToWord(self, src, dst):
        word = win32com.client.Dispatch('Word.Application')

        doc = word.Documents.Add(src)
        doc.SaveAs(dst, FileFormat=0)
        doc.Close()

        word.Quit()

    @waitCursorDecorator
    def __exportToHtml(self, fileName):
        template_name = self.templateSelector.currentText()
        report = Report.Report(self.model, template_name, fileName)
        self.fileName = report.generate(self.records, True)

    @waitCursorDecorator
    def __exportToPdf(self, fileName):
        self.printer.setOutputFormat(QPrinter.PdfFormat)
        self.printer.setOutputFileName(fileName)
        self.preview.print_()
        self.printer.setOutputFormat(QPrinter.NativeFormat)

    def _q_previewChanged(self):
        self.updateNavActions()
        self.updatePageNumLabel()
        self.updateZoomFactor()

    def _q_zoomFactorChanged(self):
        text = self.zoomFactor.lineEdit().text()

        try:
            factor = float(text.replace('%', ''))
        except ValueError:
            return

        factor = max(1.0, min(1000.0, factor))
        self.preview.setZoomFactor(factor / 100.0)
        self.zoomFactor.setEditText("%g%%" % factor)
        self.setFitting(False)
