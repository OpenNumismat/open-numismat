from PySide6.QtWidgets import QMessageBox

from PySide6.QtCore import Qt, QMargins, QT_TRANSLATE_NOOP
from PySide6.QtGui import QFont, QValidator, QIcon
from PySide6.QtWidgets import QDialog, QLabel, QDialogButtonBox, QVBoxLayout, QLayout


class BaseBarcodeDialog(QDialog):

    def __init__(self, barcode, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self._parseBarcode(barcode)

        label_grader = QLabel(f"{self.tr('Grader')}: {self.grader}")
        label_barcode = QLabel(f"{self.tr('Barcode')}: {self.barcode}")
        label_grade = QLabel(f"{self.tr('Grade')}: {self.grade}")
        label_url = QLabel(f"{self.tr('URL')}: <a href='{self.url}'>{self.url}</a>")
        label_url.setTextFormat(Qt.RichText)
        label_url.setTextInteractionFlags(Qt.TextBrowserInteraction)
        label_url.setOpenExternalLinks(True)

        self.buttonBox = QDialogButtonBox(Qt.Horizontal)
        self.buttonBox.addButton(QDialogButtonBox.Save)
        self.buttonBox.addButton(QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(label_grader)
        layout.addWidget(label_barcode)
        layout.addWidget(label_grade)
        layout.addWidget(label_url)
        layout.addWidget(self.buttonBox)
        layout.setSizeConstraint(QLayout.SetFixedSize)

        self.setLayout(layout)


class NGCBarcodeDialog(BaseBarcodeDialog):

    def __init__(self, barcode, parent=None):
        super().__init__(barcode, parent)

        self.setWindowTitle(self.tr("NGC barcode parser"))
        self.setWindowIcon(QIcon(':/ngc.png'))

    def _parseBarcode(self, barcode):
        self.barcode = f"{barcode[-10:-3]}-{barcode[-3:]}"
        self.grade = barcode[6:8]
        self.grader = "NGC"
        self.url = f"https://www.ngccoin.com/certlookup/{self.barcode}/{self.grade}/"


class PCGSBarcodeDialog(BaseBarcodeDialog):

    def __init__(self, barcode, parent=None):
        super().__init__(barcode, parent)

        self.setWindowTitle(self.tr("PCGS barcode parser"))
        self.setWindowIcon(QIcon(':/pcgs.png'))

    def _parseBarcode(self, barcode):
        self.barcode = barcode[-9:]
        self.grade = barcode[11:13]
        self.grader = "PCGS"
        self.url = f"https://www.pcgs.com/cert/{self.barcode}"


class OldPCGSBarcodeDialog(BaseBarcodeDialog):

    def __init__(self, barcode, parent=None):
        super().__init__(barcode, parent)

        self.setWindowTitle(self.tr("PCGS barcode parser"))
        self.setWindowIcon(QIcon(':/pcgs.png'))

    def _parseBarcode(self, barcode):
        self.barcode = barcode[-8:]
        self.grade = barcode[6:8]
        self.grader = "PCGS"
        self.url = f"https://www.pcgs.com/cert/{self.barcode}"


def parseBarcode(barcode, parent=None):
    result = {"barcode": barcode}

    if len(barcode) == 20 or len(barcode) == 18:  # NGC
        dlg = NGCBarcodeDialog(barcode, parent)
        if dlg.exec() == QDialog.Accepted:
            result["barcode"] = dlg.barcode
            result["grader"] = dlg.grader
            result["grade"] = dlg.grade
            result["url"] = dlg.url
        dlg.deleteLater()
    elif len(barcode) == 22:  # PCGS
        dlg = PCGSBarcodeDialog(barcode, parent)
        if dlg.exec() == QDialog.Accepted:
            result["barcode"] = dlg.barcode
            result["grader"] = dlg.grader
            result["grade"] = dlg.grade
            result["url"] = dlg.url
        dlg.deleteLater()
    elif len(barcode) == 16:  # old PCGS
        dlg = OldPCGSBarcodeDialog(barcode, parent)
        if dlg.exec() == QDialog.Accepted:
            result["barcode"] = dlg.barcode
            result["grader"] = dlg.grader
            result["grade"] = dlg.grade
            result["url"] = dlg.url
        dlg.deleteLater()

    return result
