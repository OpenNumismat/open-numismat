from PyQt5.QtCore import Qt, QSettings, QMargins, QFileInfo
from PyQt5.QtWidgets import *

import OpenNumismat


class ExportDialog(QDialog):
    IMAGE_OBVERSE = 0
    IMAGE_REVERSE = 1
    IMAGE_BOTH = 2

    latestDir = OpenNumismat.HOME_PATH
    params = {}

    def __init__(self, collection, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self.collection = collection

        self.setWindowTitle(self.tr("Export to mobile"))

        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.WrapLongRows)

        # density
        self.densitySelector = QComboBox(self)
        densities = ('MDPI', 'HDPI', 'XHDPI', 'XXHDPI', 'XXXHDPI')
        self.densitySelector.addItems(densities)
        self.densitySelector.setSizePolicy(QSizePolicy.Fixed,
                                           QSizePolicy.Fixed)
        form.addRow(self.tr("Target density of the display"), self.densitySelector)

        settings = QSettings()
        density = settings.value('density', 'XHDPI')
        self.densitySelector.setCurrentText(density)

        # filtering
        self.filterSelector = QComboBox(self)
        self.filterSelector.addItem(self.tr("Countries"), 'country')
        self.filterSelector.addItem(self.tr("Series"), 'series')
        self.filterSelector.addItem(self.tr("Denomination"), 'denomination')
        self.filterSelector.setSizePolicy(QSizePolicy.Fixed,
                                          QSizePolicy.Fixed)
        form.addRow(self.tr("Default filter by"), self.filterSelector)

        # image
        groupBox = QGroupBox(self.tr("Image"))
        vbox = QFormLayout(self)

        self.obverseRadio = QRadioButton(self.tr("Obverse"), self)
        self.reverseRadio = QRadioButton(self.tr("Reverse"), self)
        self.bothRadio = QRadioButton(self.tr("Both"), self)
        self.bothRadio.setChecked(True)

        vbox.addRow(self.obverseRadio)
        vbox.addRow(self.reverseRadio)
        vbox.addRow(self.bothRadio)

        groupBox.setLayout(vbox)
        form.addRow(groupBox)

        self.fullImage = QCheckBox(self.tr("Export a full-sized image"), self)
        form.addRow(self.fullImage)

        # file
        self.destination = QLineEdit(self)
        style = QApplication.style()
        icon = style.standardIcon(QStyle.SP_DialogOpenButton)
        self.destinationButton = QPushButton(icon, '', self)
        self.destinationButton.clicked.connect(self.destinationButtonClicked)

        hLayout = QHBoxLayout()
        hLayout.addWidget(self.destination)
        hLayout.addWidget(self.destinationButton)
        hLayout.setContentsMargins(QMargins())

        form.addRow(self.tr("Destination"), hLayout)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        self.acceptButton = buttonBox.addButton(QDialogButtonBox.Ok)
        self.acceptButton.setEnabled(False)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.start)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

        self.setFixedSize(self.sizeHint())

    def destinationButtonClicked(self):
        destination = self.destination.text()
        if not destination and self.collection:
            destination = self.latestDir + '/' + self.collection.getCollectionName() + '_mobile.db'
        file, _selectedFilter = QFileDialog.getSaveFileName(
            self, self.tr("Select destination"), destination, "*.db")
        if file:
            file_info = QFileInfo(file)
            self.latestDir = file_info.absolutePath()

            self.destination.setText(file)
            self.acceptButton.setEnabled(True)

    def start(self):
        file = self.destination.text().strip()
        if not file:
            QMessageBox.warning(self,
                              self.tr("Create mobile collection"),
                              self.tr("Destination file not specified"))
            return

        density = self.densitySelector.currentText()
        settings = QSettings()
        settings.setValue('density', density)

        self.params['filter'] = self.filterSelector.itemData(self.filterSelector.currentIndex())
        self.params['density'] = density
        self.params['file'] = file
        if self.obverseRadio.isChecked():
            self.params['image'] = self.IMAGE_OBVERSE
        elif self.reverseRadio.isChecked():
            self.params['image'] = self.IMAGE_REVERSE
        else:
            self.params['image'] = self.IMAGE_BOTH
        self.params['fullimage'] = self.fullImage.isChecked()

        self.accept()
