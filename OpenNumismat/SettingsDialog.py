# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QMargins
from PyQt5.QtWidgets import *

from OpenNumismat.EditCoinDialog.FormItems import NumberEdit
from OpenNumismat.Collection.CollectionFields import CollectionFieldsBase
from OpenNumismat.Reports import Report
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Settings import Settings
from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.Collection.Import.Colnect import ColnectCache


class MainSettingsPage(QWidget):
    Languages = (("Български", 'bg'), ("Català", 'ca'), ("Čeština", 'cs'),
                 ("Deutsch", 'de'), ("English", 'en'), ("Ελληνικά", 'el'),
                 ("Español", 'es'), ("فارسی", 'fa'), ("Français", 'fr'),
                 ("Italiano", 'it'), ("Latviešu", 'lv'), ("Magyar", 'hu'),
                 ("Nederlands", 'nl'), ("Polski", 'pl'), ("Português", 'pt'),
                 ("Русский", 'ru'), ("Svenska", 'sv'), ("Türkçe", 'tr'),
                 ("Український", 'uk'),
                 )

    def __init__(self, collection, parent=None):
        super().__init__(parent)

        settings = Settings()

        style = QApplication.style()

        layout = QFormLayout()
        layout.setRowWrapPolicy(QFormLayout.WrapLongRows)

        current = 4
        self.languageSelector = QComboBox(self)
        for i, lang in enumerate(self.Languages):
            self.languageSelector.addItem(lang[0], lang[1])
            if settings['locale'] == lang[1]:
                current = i
        self.languageSelector.setCurrentIndex(current)
        self.languageSelector.setSizePolicy(QSizePolicy.Fixed,
                                            QSizePolicy.Fixed)

        layout.addRow(self.tr("Language"), self.languageSelector)

        self.reference = QLineEdit(self)
        self.reference.setMinimumWidth(120)
        self.reference.setText(settings['reference'])
        icon = style.standardIcon(QStyle.SP_DialogOpenButton)
        self.referenceButton = QPushButton(icon, '', self)
        self.referenceButton.clicked.connect(self.referenceButtonClicked)
        if collection.isReferenceAttached():
            self.reference.setDisabled(True)
            self.referenceButton.setDisabled(True)

        hLayout = QHBoxLayout()
        hLayout.addWidget(self.reference)
        hLayout.addWidget(self.referenceButton)
        hLayout.setContentsMargins(QMargins())

        layout.addRow(self.tr("Reference"), hLayout)

        self.backupFolder = QLineEdit(self)
        self.backupFolder.setMinimumWidth(120)
        self.backupFolder.setText(settings['backup'])
        icon = style.standardIcon(QStyle.SP_DirOpenIcon)
        self.backupFolderButton = QPushButton(icon, '', self)
        self.backupFolderButton.clicked.connect(self.backupButtonClicked)

        hLayout = QHBoxLayout()
        hLayout.addWidget(self.backupFolder)
        hLayout.addWidget(self.backupFolderButton)
        hLayout.setContentsMargins(QMargins())

        layout.addRow(self.tr("Backup folder"), hLayout)

        self.autobackup = QCheckBox(self.tr("Make autobackup"), self)
        self.autobackup.setChecked(settings['autobackup'])
        self.autobackup.stateChanged.connect(self.autobackupClicked)
        layout.addRow(self.autobackup)

        self.autobackupDepth = QSpinBox(self)
        self.autobackupDepth.setRange(1, 1000)
        self.autobackupDepth.setValue(settings['autobackup_depth'])
        self.autobackupDepth.setSizePolicy(QSizePolicy.Fixed,
                                           QSizePolicy.Fixed)
        layout.addRow(self.tr("Coin changes before autobackup"),
                      self.autobackupDepth)
        self.autobackupDepth.setEnabled(settings['autobackup'])

        self.errorSending = QCheckBox(
                            self.tr("Send error info to author"), self)
        self.errorSending.setChecked(settings['error'])
        layout.addRow(self.errorSending)

        self.checkUpdates = QCheckBox(
                            self.tr("Automatically check for updates"), self)
        self.checkUpdates.setChecked(settings['updates'])
        layout.addRow(self.checkUpdates)

        self.speedup = QComboBox(self)
        self.speedup.addItem(self.tr("Reliable"), 0)
        self.speedup.addItem(self.tr("Fast"), 1)
        self.speedup.addItem(self.tr("Extra fast (dangerous)"), 2)
        self.speedup.setCurrentIndex(settings['speedup'])
        self.speedup.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addRow(self.tr("Acceleration of storage"), self.speedup)

        self.checkTitle = QCheckBox(
                        self.tr("Check that coin title present on save"), self)
        self.checkTitle.setChecked(settings['check_coin_title'])
        layout.addRow(self.checkTitle)

        self.checkDuplicate = QCheckBox(
                        self.tr("Check coin duplicates on save"), self)
        self.checkDuplicate.setChecked(settings['check_coin_duplicate'])
        layout.addRow(self.checkDuplicate)

        current = 0
        self.templateSelector = QComboBox(self)
        for i, template in enumerate(Report.scanTemplates()):
            self.templateSelector.addItem(template[0], template[1])
            if settings['template'] == template[1]:
                current = i
        self.templateSelector.setCurrentIndex(current)
        self.templateSelector.setSizePolicy(QSizePolicy.Fixed,
                                            QSizePolicy.Fixed)

        layout.addRow(self.tr("Default template"), self.templateSelector)

        self.imagesByDefault = QSpinBox(self)
        self.imagesByDefault.setRange(1, 8)
        self.imagesByDefault.setValue(settings['images_by_default'])
        self.imagesByDefault.setSizePolicy(QSizePolicy.Fixed,
                                           QSizePolicy.Fixed)
        layout.addRow(self.tr("Images count by default"), self.imagesByDefault)

        current = 0
        self.mapSelector = QComboBox(self)
        self.mapSelector.addItem('OpenStreetMap')
        self.mapSelector.addItem('Google Maps')
        self.mapSelector.setCurrentIndex(settings['map_type'])
        self.mapSelector.setSizePolicy(QSizePolicy.Fixed,
                                       QSizePolicy.Fixed)
        layout.addRow(self.tr("Maps"), self.mapSelector)

        self.verifySsl = QCheckBox(
                        self.tr("Verify SSL certifiacte"), self)
        self.verifySsl.setChecked(settings['verify_ssl'])
        layout.addRow(self.verifySsl)

        self.setLayout(layout)

    def backupButtonClicked(self):
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Backup folder"), self.backupFolder.text())
        if folder:
            self.backupFolder.setText(folder)

    def autobackupClicked(self, state):
        self.autobackupDepth.setEnabled(state == Qt.Checked)

    def referenceButtonClicked(self):
        file, _selectedFilter = QFileDialog.getOpenFileName(
            self, self.tr("Select reference"), self.reference.text(), "*.ref")
        if file:
            self.reference.setText(file)

    def save(self):
        settings = Settings()

        settings['locale'] = self.languageSelector.currentData()
        settings['backup'] = self.backupFolder.text()
        settings['autobackup'] = self.autobackup.isChecked()
        settings['autobackup_depth'] = self.autobackupDepth.value()
        settings['reference'] = self.reference.text()
        settings['error'] = self.errorSending.isChecked()
        settings['updates'] = self.checkUpdates.isChecked()
        settings['speedup'] = self.speedup.currentData()
        settings['template'] = self.templateSelector.currentData()
        settings['check_coin_title'] = self.checkTitle.isChecked()
        settings['check_coin_duplicate'] = self.checkDuplicate.isChecked()
        settings['images_by_default'] = self.imagesByDefault.value()
        settings['map_type'] = self.mapSelector.currentIndex()
        settings['verify_ssl'] = self.verifySsl.isChecked()

        settings.save()


class CollectionSettingsPage(QWidget):

    def __init__(self, collection, parent=None):
        super().__init__(parent)

        self.settings = collection.settings
        self.model = collection.model()

        layout = QFormLayout()
        layout.setRowWrapPolicy(QFormLayout.WrapLongRows)

        self.imageSideLen = NumberEdit(self)
        self.imageSideLen.setMaximumWidth(60)
        layout.addRow(self.tr("Max image side len"), self.imageSideLen)
        self.imageSideLen.setText(str(self.settings['ImageSideLen']))
        self.imageSideLen.setToolTip(self.tr("0 for storing in original size"))

        self.imageHeight = QDoubleSpinBox(self)
        self.imageHeight.setRange(1, 3)
        self.imageHeight.setDecimals(1)
        self.imageHeight.setSingleStep(0.1)
        self.imageHeight.setValue(self.settings['image_height'])
        self.imageHeight.setSizePolicy(QSizePolicy.Fixed,
                                       QSizePolicy.Fixed)
        layout.addRow(self.tr("Preview image height"), self.imageHeight)

        self.freeNumeric = QCheckBox(
                            self.tr("Free format numeric fields"), self)
        self.freeNumeric.setChecked(self.settings['free_numeric'])
        layout.addRow(self.freeNumeric)

        self.convertFraction = QCheckBox(
            self.tr("Convert 0.5 to ½ (support ¼, ⅓, ½, ¾, 1¼, 1½, 2½)"), self)
        self.convertFraction.setChecked(self.settings['convert_fraction'])
        layout.addRow(self.convertFraction)

        self.storeSorting = QCheckBox(
                            self.tr("Store column sorting"), self)
        self.storeSorting.setChecked(self.settings['store_sorting'])
        layout.addRow(self.storeSorting)

        self.imagesAtBottom = QCheckBox(self.tr("Images at bottom"), self)
        self.imagesAtBottom.setChecked(self.settings['images_at_bottom'])
        layout.addRow(self.imagesAtBottom)

        self.enableBC = QCheckBox(self.tr("Enable BC"), self)
        self.enableBC.setChecked(self.settings['enable_bc'])
        layout.addRow(self.enableBC)

        self.richText = QCheckBox(self.tr("Use RichText format"), self)
        self.richText.setChecked(self.settings['rich_text'])
        layout.addRow(self.richText)

        vLayout = QVBoxLayout()
        showIcons = QGroupBox(self.tr("Show icons from reference (slow)"), self)
        self.showTreeIcons = QCheckBox(self.tr("in tree"), self)
        self.showTreeIcons.setChecked(self.settings['show_tree_icons'])
        vLayout.addWidget(self.showTreeIcons)
        self.showFilterIcons = QCheckBox(self.tr("in filters"), self)
        self.showFilterIcons.setChecked(self.settings['show_filter_icons'])
        vLayout.addWidget(self.showFilterIcons)
        self.showListIcons = QCheckBox(self.tr("in list"), self)
        self.showListIcons.setChecked(self.settings['show_list_icons'])
        vLayout.addWidget(self.showListIcons)
        showIcons.setLayout(vLayout)
        layout.addRow(showIcons)

        gLayout = QGridLayout()
        statuses = QGroupBox(self.tr("Used statuses"), self)
        self.statusUsed = {}
        statuses_per_col = len(Statuses.Keys) / 4
        for i, status in enumerate(Statuses.Keys):
            statusCheckBox = QCheckBox(Statuses[status], self)
            statusCheckBox.setChecked(self.settings[status + '_status_used'])
            self.statusUsed[status] = statusCheckBox
            gLayout.addWidget(statusCheckBox, i % statuses_per_col, i / statuses_per_col)
        statuses.setLayout(gLayout)
        layout.addRow(statuses)

        self.defaultStatus = QComboBox(self)
        for status in Statuses.Keys:
            self.defaultStatus.addItem(Statuses[status], status)
        index = self.defaultStatus.findData(self.settings['default_status'])
        self.defaultStatus.setCurrentIndex(index)
        self.defaultStatus.setSizePolicy(QSizePolicy.Fixed,
                                         QSizePolicy.Fixed)
        layout.addRow(self.tr("Default status for new coin"),
                      self.defaultStatus)

        self.setLayout(layout)

    def save(self):
        self.settings['free_numeric'] = self.freeNumeric.isChecked()
        self.settings['convert_fraction'] = self.convertFraction.isChecked()
        self.settings['store_sorting'] = self.storeSorting.isChecked()
        self.settings['show_tree_icons'] = self.showTreeIcons.isChecked()
        self.settings['show_filter_icons'] = self.showFilterIcons.isChecked()
        self.settings['show_list_icons'] = self.showListIcons.isChecked()
        self.settings['ImageSideLen'] = int(self.imageSideLen.text())
        old_image_height = self.settings['image_height']
        self.settings['image_height'] = self.imageHeight.value()
        self.settings['images_at_bottom'] = self.imagesAtBottom.isChecked()
        self.settings['enable_bc'] = self.enableBC.isChecked()
        self.settings['rich_text'] = self.richText.isChecked()
        self.settings['default_status'] = self.defaultStatus.currentData()

        for status in Statuses.Keys:
            self.settings[status + '_status_used'] = self.statusUsed[status].isChecked()

        self.settings.save()

        if self.settings['image_height'] != old_image_height:
            result = QMessageBox.question(self, self.tr("Settings"),
                    self.tr("Preview image height was changed. Recalculate it now?"),
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if result == QMessageBox.Yes:
                self.model.recalculateAllImages(self)


class FieldsSettingsPage(QWidget):
    DataRole = Qt.UserRole

    def __init__(self, collection, parent=None):
        super().__init__(parent)

        self.listWidget = QListWidget(self)
        self.listWidget.setWrapping(True)
        self.listWidget.setMinimumWidth(330)
        self.listWidget.setMinimumHeight(180)
        self.listWidget.itemSelectionChanged.connect(self.itemSelectionChanged)

        self.fields = collection.fields
        for field in self.fields:
            item = QListWidgetItem(field.title)
            item.setData(self.DataRole, field)
            item.setFlags(Qt.ItemIsEditable | Qt.ItemIsUserCheckable |
                          Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            checked = Qt.Unchecked
            if field.enabled:
                checked = Qt.Checked
            item.setCheckState(checked)
            self.listWidget.addItem(item)

        self.renameButton = QPushButton(self.tr("Rename"), self)
        self.renameButton.clicked.connect(self.renameButtonClicked)
        self.renameButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.renameButton.setEnabled(False)

        self.defaultFieldsButton = QPushButton(
                                            self.tr("Revert to default"), self)
        self.defaultFieldsButton.clicked.connect(
                                            self.defaultFieldsButtonClicked)
        self.defaultFieldsButton.setSizePolicy(QSizePolicy.Fixed,
                                               QSizePolicy.Fixed)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(self.tr("Global enabled fields:"), self))
        layout.addWidget(self.listWidget)

        hLayout = QHBoxLayout()
        hLayout.addWidget(self.renameButton, alignment=Qt.AlignLeft)
        hLayout.addWidget(self.defaultFieldsButton, alignment=Qt.AlignRight)
        layout.addLayout(hLayout)

        self.setLayout(layout)

    def itemSelectionChanged(self):
        self.renameButton.setEnabled(len(self.listWidget.selectedItems()) > 0)

    def resizeEvent(self, _):
        self.listWidget.setWrapping(True)

    def defaultFieldsButtonClicked(self):
        defaultFields = CollectionFieldsBase()
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            field = item.data(self.DataRole)
            defaultField = defaultFields.field(field.id)
            item.setText(defaultField.title)

    def renameButtonClicked(self):
        items = self.listWidget.selectedItems()
        if len(items) > 0:
            self.listWidget.editItem(items[0])

    def save(self):
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            field = item.data(self.DataRole)
            field.enabled = (item.checkState() == Qt.Checked)
            field.title = item.text()

        self.fields.save()


class ColnectSettingsPage(QWidget):
    Languages = (
        ('ar', 'العربية'), ('az', 'Azərbaycanca'), ('be', 'Беларуская'),
        ('bg', 'Български'), ('ca', 'Català'), ('cs', 'Česky'),
        ('da', 'Dansk'), ('de', 'Deutsch'), ('el', 'Ελληνικά'),
        ('en', 'English'), ('es', 'Español'), ('et', 'Eesti'), ('fa', 'فارسی'),
        ('fr', 'Français'), ('ko', '한국어'), ('hr', 'Hrvatski'),
        ('id', 'Bahasa Indonesia'), ('it', 'Italiano'), ('he', 'עברית'),
        ('ka', 'ქართული '), ('lv', 'Latviešu'), ('lt', 'Lietuvių'),
        ('hu', 'Magyar'), ('nl', 'Nederlands'), ('ja', '日本語'),
        ('no', 'Norsk'), ('pl', 'Polski'), ('pt', 'Português'),
        ('br', 'Português BR'), ('ro', 'Română'), ('ru', 'Русский'),
        ('sk', 'Slovenčina'), ('sl', 'Slovenščina'), ('sr', 'Српски'),
        ('fi', 'Suomi'), ('sv', 'Svenska'), ('th', 'ภาษาไทย '),
        ('tr', 'Türkçe'), ('uk', 'Українська'), ('vi', 'Tiếng Việt'),
        ('zh', '中文（简体）'), ('zt', '中文 (繁體)'),
        # ('ky', 'Кыргызча'), ('ta', 'தமிழ்'), ('hy', 'Հայերեն'),
        # ('sw', 'Kiswahili'), ('bn', 'বাংলা'), ('si', 'සිංහල'), ('gu', 'ગુજરાતી'),
        # ('ht', 'Kreyòl ayisyen'), ('mn', 'Монгол'), ('sq', 'Shqip'),
        # ('af', 'Afrikaans'), ('te', 'తెలుగు'), ('ml', 'മലയാളം'), ('hi', 'हिन्दी'),
        # ('tl', 'Filipino'), ('ms', 'Melayu'), ('pa', 'پنجابی'),
        # ('kk', 'Қазақша'), ('ur', 'اردو'), ('mk', 'Македонски'),
        # ('fy', 'Frysk'),
    )

    def __init__(self, collection, parent=None):
        super().__init__(parent)

        settings = Settings()

        fLayout = QFormLayout()
        fLayout.setRowWrapPolicy(QFormLayout.WrapLongRows)

        default_locale = settings['colnect_locale']
        current = 9
        self.languageSelector = QComboBox(self)
        for i, lang in enumerate(self.Languages):
            self.languageSelector.addItem(lang[1], lang[0])
            if default_locale == lang[0]:
                current = i
        self.languageSelector.setCurrentIndex(current)
        self.languageSelector.setSizePolicy(QSizePolicy.Fixed,
                                            QSizePolicy.Fixed)

        fLayout.addRow(self.tr("Language"), self.languageSelector)

        self.autoclose = QCheckBox(self.tr("Close dialog after adding item"),
                                   self)
        self.autoclose.setChecked(settings['colnect_autoclose'])
        fLayout.addRow(self.autoclose)

        self.skip_currency = QCheckBox(self.tr("Skip currency symbol"),
                                       self)
        self.skip_currency.setChecked(settings['colnect_skip_currency'])
        fLayout.addRow(self.skip_currency)

        clearCacheBtn = QPushButton(self.tr("Clear cache"), self)
        clearCacheBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        clearCacheBtn.clicked.connect(self.clearCache)

        hLayout = QHBoxLayout()
        hLayout.addWidget(clearCacheBtn, alignment=Qt.AlignRight)

        vLayout = QVBoxLayout()
        vLayout.addLayout(fLayout)
        vLayout.addLayout(hLayout)

        self.enabledGroup = QGroupBox(self.tr("Use Colnect"), self)
        self.enabledGroup.setCheckable(True)
        self.enabledGroup.setChecked(settings['colnect_enabled'])
        self.enabledGroup.setLayout(vLayout)

        layout = QVBoxLayout()
        layout.addWidget(self.enabledGroup)

        self.setLayout(layout)

    def clearCache(self):
        ColnectCache.clear()

    def save(self):
        settings = Settings()

        settings['colnect_enabled'] = self.enabledGroup.isChecked()
        settings['colnect_locale'] = self.languageSelector.currentData()
        settings['colnect_autoclose'] = self.autoclose.isChecked()
        settings['colnect_skip_currency'] = self.skip_currency.isChecked()

        settings.save()


@storeDlgSizeDecorator
class SettingsDialog(QDialog):
    def __init__(self, collection, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        mainPage = MainSettingsPage(collection, self)
        collectionPage = CollectionSettingsPage(collection, self)
        fieldsPage = FieldsSettingsPage(collection, self)
        colnectPage = ColnectSettingsPage(collection, self)

        self.setWindowTitle(self.tr("Settings"))

        self.tab = QTabWidget(self)
        self.tab.addTab(mainPage, self.tr("Main"))
        index = self.tab.addTab(collectionPage, self.tr("Collection"))
        if not collection.isOpen():
            self.tab.setTabEnabled(index, False)
        index = self.tab.addTab(fieldsPage, self.tr("Fields"))
        if not collection.isOpen():
            self.tab.setTabEnabled(index, False)
        index = self.tab.addTab(colnectPage, "Colnect")
        if not collection.isOpen():
            self.tab.setTabEnabled(index, False)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.tab)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def save(self):
        for i in range(self.tab.count()):
            page = self.tab.widget(i)
            page.save()

        self.accept()
