# -*- coding: utf-8 -*-

from PySide6.QtCharts import QChart
from PySide6.QtCore import Qt, QMargins, QT_TRANSLATE_NOOP
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import *

from OpenNumismat.EditCoinDialog.FormItems import NumberEdit
from OpenNumismat.Collection.CollectionFields import CollectionFieldsBase
from OpenNumismat.Reports import Report
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Tools.Gui import statusIcon
from OpenNumismat.Tools.Gui import infoMessageBox
from OpenNumismat.Settings import Settings
from OpenNumismat.Collection.CollectionFields import Statuses, TitleTemplateFields
from OpenNumismat.Collection.Import.Cache import Cache
from OpenNumismat.EditCoinDialog.MapWidget import MapType
from OpenNumismat.EditCoinDialog.MapWidget.GMapsWidget import gmapsAvailable
from OpenNumismat.EditCoinDialog.MapWidget.MapboxWidget import mapboxAvailable


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

        self.languageSelector = QComboBox(self)
        for lang in self.Languages:
            self.languageSelector.addItem(lang[0], lang[1])
        current = self.languageSelector.findData(settings['locale'])
        if current == -1:
            current = 4
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

        self.templateSelector = QComboBox(self)
        for template in Report.scanTemplates():
            self.templateSelector.addItem(template[0], template[1])
        current = self.templateSelector.findData(settings['template'])
        if current == -1:
            current = 0
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

        self.builtInViewer = QCheckBox(
                        self.tr("Use built-in image viewer"), self)
        self.builtInViewer.setChecked(settings['built_in_viewer'])
        layout.addRow(self.builtInViewer)

        self.mapSelector = QComboBox(self)
        self.mapSelector.addItem('OpenStreetMap', MapType.OSM.value)
        if gmapsAvailable:
            self.mapSelector.addItem('Google Maps', MapType.GMaps.value)
        if mapboxAvailable:
            self.mapSelector.addItem('Mapbox', MapType.Mapbox.value)
        self.mapSelector.addItem('Roman Empire (DARE)', MapType.DARE.value)
        current = self.mapSelector.findData(settings['map_type'])
        if current == -1:
            current = MapType.OSM.value
        self.mapSelector.setCurrentIndex(current)
        self.mapSelector.setSizePolicy(QSizePolicy.Fixed,
                                       QSizePolicy.Fixed)
        layout.addRow(self.tr("Maps"), self.mapSelector)

        self.styleSelector = QComboBox(self)
        for key in QStyleFactory.keys():
            self.styleSelector.addItem(key)
        self.styleSelector.setCurrentText(settings['style'])
        self.styleSelector.setSizePolicy(QSizePolicy.Fixed,
                                         QSizePolicy.Fixed)
        layout.addRow(self.tr("Style"), self.styleSelector)

        self.fontSizeSelector = QComboBox(self)
        self.fontSizeSelector.addItem(self.tr("Normal"))
        self.fontSizeSelector.addItem(self.tr("Large"))
        self.fontSizeSelector.addItem(self.tr("Huge"))
        self.fontSizeSelector.setCurrentIndex(settings['font_size'])
        self.fontSizeSelector.setSizePolicy(QSizePolicy.Fixed,
                                            QSizePolicy.Fixed)
        layout.addRow(self.tr("Font size"), self.fontSizeSelector)

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
        settings['images_by_default'] = self.imagesByDefault.value()
        settings['map_type'] = self.mapSelector.currentData()
        settings['built_in_viewer'] = self.builtInViewer.isChecked()
        settings['style'] = self.styleSelector.currentText()
        settings['font_size'] = self.fontSizeSelector.currentIndex()

        settings.save()


class FieldAction(QAction):
    clicked = pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.triggered.connect(self.trigger)

    def trigger(self):
        self.clicked.emit(self)


class CollectionSettingsPage(QWidget):

    def __init__(self, collection, parent=None):
        super().__init__(parent)

        self.collection = collection
        self.settings = collection.settings
        self.model = collection.model()

        layout = QFormLayout()
        layout.setRowWrapPolicy(QFormLayout.WrapLongRows)

        self.titleTemplate = QLineEdit(self)
        self.titleTemplate.setText(str(self.settings['title_template']))

        self.addFieldButton = QPushButton(QIcon(':/add.png'), '', self)
        self.addFieldButton.setToolTip(self.tr("Add field"))

        menu = QMenu(self)
        menu.aboutToShow.connect(self.addFieldButtonClicked)
        self.addFieldButton.setMenu(menu)

        hLayout = QHBoxLayout()
        hLayout.addWidget(self.titleTemplate)
        hLayout.addWidget(self.addFieldButton)
        hLayout.setContentsMargins(QMargins())

        layout.addRow(self.tr("Title template"), hLayout)

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

        self.imagesAtBottom = QCheckBox(self.tr("Images at bottom"), self)
        self.imagesAtBottom.setChecked(self.settings['images_at_bottom'])
        layout.addRow(self.imagesAtBottom)

        self.freeNumeric = QCheckBox(
                            self.tr("Free format numeric fields"), self)
        self.freeNumeric.setChecked(self.settings['free_numeric'])
        layout.addRow(self.freeNumeric)

        self.convertFraction = QCheckBox(
            self.tr("Convert 0.5 to ½ (support ¼, ⅓, ½, ¾, 1¼, 1½, 2½)"), self)
        self.convertFraction.setChecked(self.settings['convert_fraction'])
        layout.addRow(self.convertFraction)

        self.enableBC = QCheckBox(self.tr("Enable BC"), self)
        self.enableBC.setChecked(self.settings['enable_bc'])
        layout.addRow(self.enableBC)

        self.richText = QCheckBox(self.tr("Use RichText format"), self)
        self.richText.setChecked(self.settings['rich_text'])
        layout.addRow(self.richText)

        self.statusUsed = {}
        statusesList = QListWidget(self)
        statusesList.setWrapping(True)
        for status in Statuses:
            title = self.settings[status + '_status_title']
            item = QListWidgetItem(statusIcon(status), title)
            item.setFlags(Qt.ItemIsEditable | Qt.ItemIsUserCheckable |
                          Qt.ItemIsEnabled | Qt.ItemIsSelectable)

            checked = Qt.Unchecked
            if self.settings[status + '_status_used']:
                checked = Qt.Checked
            item.setCheckState(checked)
            statusesList.addItem(item)
            self.statusUsed[status] = item
        layout.addRow(self.tr("Used statuses:"), QWidget())
        layout.addRow(statusesList)

        self.defaultStatus = QComboBox(self)
        for status in Statuses:
            self.defaultStatus.addItem(statusIcon(status), Statuses[status], status)
        index = self.defaultStatus.findData(self.settings['default_status'])
        self.defaultStatus.setCurrentIndex(index)
        self.defaultStatus.setSizePolicy(QSizePolicy.Fixed,
                                         QSizePolicy.Fixed)
        layout.addRow(self.tr("Default status for new coin"),
                      self.defaultStatus)

        self.setLayout(layout)

    def addFieldButtonClicked(self):
        self.addFieldButton.menu().clear()
        for field in self.collection.fields:
            if field.name in TitleTemplateFields:
                if field.enabled:
                    act = FieldAction(field.title, self)
                    act.setData(field.name)
                    self.addFieldButton.menu().addAction(act)
                    act.clicked.connect(self.addField)

    def addField(self, act):
        field = act.data()
        pos = self.titleTemplate.cursorPosition()
        template = self.titleTemplate.text()
        template = template[:pos] + '<' + field + '>' + template[pos:]
        self.titleTemplate.setText(template)

    def save(self):
        self.settings['title_template'] = self.titleTemplate.text()
        self.settings['free_numeric'] = self.freeNumeric.isChecked()
        self.settings['convert_fraction'] = self.convertFraction.isChecked()
        self.settings['ImageSideLen'] = int(self.imageSideLen.text())
        old_image_height = self.settings['image_height']
        self.settings['image_height'] = self.imageHeight.value()
        self.settings['images_at_bottom'] = self.imagesAtBottom.isChecked()
        self.settings['enable_bc'] = self.enableBC.isChecked()
        self.settings['rich_text'] = self.richText.isChecked()
        default_status = self.defaultStatus.currentData()
        self.settings['default_status'] = default_status

        for status in Statuses:
            title = self.statusUsed[status].text()
            self.settings[status + '_status_title'] = title

            is_checked = (self.statusUsed[status].checkState() == Qt.Checked)
            self.settings[status + '_status_used'] = is_checked
        # Default status is always enabled
        self.settings[default_status + '_status_used'] = True

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

        self.treeWidget = QTreeWidget(self)
        self.treeWidget.setHeaderHidden(True)
        self.treeWidget.itemSelectionChanged.connect(self.itemSelectionChanged)

        image_item = QTreeWidgetItem((self.tr("Images"),))
        main_item = QTreeWidgetItem((self.tr("Main details"),))
        state_item = QTreeWidgetItem((self.tr("State"),))
        buy_item = QTreeWidgetItem((self.tr("Buy"),))
        sale_item = QTreeWidgetItem((self.tr("Sale"),))
        map_item = QTreeWidgetItem((self.tr("Map"),))
        parameters_item = QTreeWidgetItem((self.tr("Parameters"),))
        design_item = QTreeWidgetItem((self.tr("Design"),))
        classification_item = QTreeWidgetItem((self.tr("Classification"),))
        system_item = QTreeWidgetItem((self.tr("System"),))
        other_item = QTreeWidgetItem((self.tr("Other"),))

        self.fields = collection.fields
        for field in self.fields:
            item = QTreeWidgetItem((field.title,))
            item.setData(0, self.DataRole, field)
            item.setFlags(Qt.ItemIsEditable | Qt.ItemIsUserCheckable |
                          Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            checked = Qt.Unchecked
            if field.enabled:
                checked = Qt.Checked
            item.setCheckState(0, checked)

            if field.name in ('id', 'createdat', 'updatedat', 'sort_id'):
                system_item.addChild(item)
            elif field.name in ('image', 'obverseimg', 'reverseimg', 'edgeimg',
                                'photo1', 'photo2', 'photo3', 'photo4',
                                'photo5', 'photo6',
                                'varietyimg', 'signatureimg'):
                image_item.addChild(item)
            elif field.name in ('title', 'region', 'country', 'period',
                                'emitent', 'ruler', 'value', 'unit', 'year',
                                'mintmark', 'mint', 'type', 'series',
                                'subjectshort', 'native_year'):
                main_item.addChild(item)
            elif field.name in ('status', 'grade', 'quantity', 'format',
                                'condition', 'storage', 'barcode', 'defect',
                                'features', 'grader', 'seat'):
                state_item.addChild(item)
            elif field.name in ('paydate', 'payprice', 'totalpayprice',
                                'saller', 'payplace', 'payinfo'):
                buy_item.addChild(item)
            elif field.name in ('saledate', 'saleprice', 'totalsaleprice',
                                'buyer', 'saleplace', 'saleinfo'):
                sale_item.addChild(item)
            elif field.name in ('address', 'latitude', 'longitude'):
                map_item.addChild(item)
            elif field.name in ('material', 'fineness', 'weight', 'diameter',
                                'thickness', 'shape', 'obvrev', 'issuedate',
                                'mintage', 'dateemis', 'quality', 'note'):
                parameters_item.addChild(item)
            elif field.name in ('obversedesign', 'obversedesigner', 'obverseengraver',
                                'obversecolor', 'reversedesign', 'reversedesigner',
                                'reverseengraver', 'reversecolor', 'edge', 'edgelabel',
                                'signaturetype', 'signature', 'subject'):
                design_item.addChild(item)
            elif field.name in ('catalognum1', 'catalognum2', 'catalognum3', 'catalognum4',
                                'rarity', 'price4', 'price3', 'price2', 'price1',
                                'variety', 'varietydesc', 'obversevar',
                                'reversevar', 'edgevar', 'url'):
                classification_item.addChild(item)
            elif field.name in ('address', 'latitude', 'longitude'):
                map_item.addChild(item)
            else:
                other_item.addChild(item)

        for item in (image_item, main_item, state_item, buy_item, sale_item,
                     map_item, parameters_item, design_item,
                     classification_item, system_item, other_item):
            if item.childCount() > 0:
                self.treeWidget.addTopLevelItem(item)
                item.setExpanded(True)

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
        layout.addWidget(self.treeWidget)

        hLayout = QHBoxLayout()
        hLayout.addWidget(self.renameButton, alignment=Qt.AlignLeft)
        hLayout.addWidget(self.defaultFieldsButton, alignment=Qt.AlignRight)
        layout.addLayout(hLayout)

        self.setLayout(layout)

    def itemSelectionChanged(self):
        self.renameButton.setEnabled(len(self.treeWidget.selectedItems()) > 0)

    def defaultFieldsButtonClicked(self):
        defaultFields = CollectionFieldsBase()
        for i in range(self.treeWidget.topLevelItemCount()):
            top_item = self.treeWidget.topLevelItem(i)
            for j in range(top_item.childCount()):
                item = top_item.child(j)
                field = item.data(0, self.DataRole)
                defaultField = defaultFields.field(field.id)
                item.setText(0, defaultField.title)

    def renameButtonClicked(self):
        items = self.treeWidget.selectedItems()
        if len(items) > 0:
            self.treeWidget.editItem(items[0])

    def save(self):
        for i in range(self.treeWidget.topLevelItemCount()):
            top_item = self.treeWidget.topLevelItem(i)
            for j in range(top_item.childCount()):
                item = top_item.child(j)
                field = item.data(0, self.DataRole)
                field.enabled = (item.checkState(0) == Qt.Checked)
                field.title = item.text(0)

        self.fields.save()


class ImportSettingsPage(QWidget):
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
    Currencies = (('BGN', QT_TRANSLATE_NOOP("Currency", "BGN - Bulgarian lev")),
                  ('BRL', QT_TRANSLATE_NOOP("Currency", "BRL - Brazilian real")),
                  ('BYN', QT_TRANSLATE_NOOP("Currency", "BYN - Belarusian ruble")),
                  ('CZK', QT_TRANSLATE_NOOP("Currency", "CZK - Czech koruna")),
                  ('EUR', QT_TRANSLATE_NOOP("Currency", "EUR - Euro")),
                  ('GBP', QT_TRANSLATE_NOOP("Currency", "GBP - Pound sterling")),
                  ('HUF', QT_TRANSLATE_NOOP("Currency", "HUF - Hungarian forint")),
                  ('PLN', QT_TRANSLATE_NOOP("Currency", "PLN - Polish złoty")),
                  ('RUB', QT_TRANSLATE_NOOP("Currency", "RUB - Russian ruble")),
                  ('SEK', QT_TRANSLATE_NOOP("Currency", "SEK - Swedish krona")),
                  ('TRY', QT_TRANSLATE_NOOP("Currency", "TRY - Turkish lira")),
                  ('UAH', QT_TRANSLATE_NOOP("Currency", "UAH - Ukrainian hryvnia")),
                  ('USD', QT_TRANSLATE_NOOP("Currency", "USD - United States dollar")))

    def __init__(self, parent=None):
        super().__init__(parent)

        settings = Settings()

        fLayout = QFormLayout()
        fLayout.setRowWrapPolicy(QFormLayout.WrapLongRows)

        self.colnect_locale = QComboBox(self)
        for lang in self.Languages:
            self.colnect_locale.addItem(lang[1], lang[0])
        current = self.colnect_locale.findData(settings['colnect_locale'])
        if current == -1:
            current = 9
        self.colnect_locale.setCurrentIndex(current)
        self.colnect_locale.setSizePolicy(QSizePolicy.Fixed,
                                            QSizePolicy.Fixed)

        fLayout.addRow(self.tr("Language"), self.colnect_locale)

        self.skip_currency = QCheckBox(self.tr("Skip currency symbol"),
                                       self)
        self.skip_currency.setChecked(settings['colnect_skip_currency'])
        fLayout.addRow(self.skip_currency)

        vLayout = QVBoxLayout()
        vLayout.addLayout(fLayout)

        colnectGroup = QGroupBox("Colnect", self)
        colnectGroup.setLayout(vLayout)

        fLayout = QFormLayout()
        fLayout.setRowWrapPolicy(QFormLayout.WrapLongRows)

        self.ans_locale_en = QCheckBox(self.tr("English language"), self)
        self.ans_locale_en.setChecked(settings['ans_locale_en'])
        fLayout.addRow(self.ans_locale_en)

        self.ans_split_denomination = QCheckBox(self.tr("Split denomination"), self)
        self.ans_split_denomination.setChecked(settings['ans_split_denomination'])
        fLayout.addRow(self.ans_split_denomination)

        self.ans_trim_title = QCheckBox(self.tr("Trim ID in title"), self)
        self.ans_trim_title.setChecked(settings['ans_trim_title'])
        fLayout.addRow(self.ans_trim_title)

        vLayout = QVBoxLayout()
        vLayout.addLayout(fLayout)

        ansGroup = QGroupBox("American Numismatic Society", self)
        ansGroup.setLayout(vLayout)

        fLayout = QFormLayout()
        fLayout.setRowWrapPolicy(QFormLayout.WrapLongRows)

        self.numista_split_denomination = QCheckBox(self.tr("Split denomination"), self)
        self.numista_split_denomination.setChecked(settings['numista_split_denomination'])
        fLayout.addRow(self.numista_split_denomination)

        self.numista_currency = QComboBox(self)
        for curr in self.Currencies:
            self.numista_currency.addItem(QApplication.translate("Currency", curr[1]), curr[0])
        current = self.numista_currency.findData(settings['numista_currency'])
        if current == -1:
            current = 4
        self.numista_currency.setCurrentIndex(current)
        self.numista_currency.setSizePolicy(QSizePolicy.Fixed,
                                            QSizePolicy.Fixed)
        fLayout.addRow(self.tr("Price currency"), self.numista_currency)

        vLayout = QVBoxLayout()
        vLayout.addLayout(fLayout)

        numistaGroup = QGroupBox("Numista", self)
        numistaGroup.setLayout(vLayout)

        clearCacheBtn = QPushButton(self.tr("Clear cache"), self)
        clearCacheBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        clearCacheBtn.clicked.connect(self.clearCache)

        hLayout = QHBoxLayout()
        hLayout.addWidget(clearCacheBtn, alignment=Qt.AlignRight)

        layout = QVBoxLayout()
        layout.addWidget(colnectGroup)
        layout.addWidget(ansGroup)
        layout.addWidget(numistaGroup)
        layout.addLayout(hLayout)

        self.setLayout(layout)

    def clearCache(self):
        Cache.clear()

        infoMessageBox("clear", self.tr("Clear cache"),
                       self.tr("Import cache cleared"),
                       parent=self)

    def save(self):
        settings = Settings()

        settings['colnect_locale'] = self.colnect_locale.currentData()
        settings['colnect_skip_currency'] = self.skip_currency.isChecked()
        settings['ans_split_denomination'] = self.ans_split_denomination.isChecked()
        settings['ans_locale_en'] = self.ans_locale_en.isChecked()
        settings['ans_trim_title'] = self.ans_trim_title.isChecked()
        settings['numista_split_denomination'] = self.numista_split_denomination.isChecked()
        settings['numista_currency'] = self.numista_currency.currentData()

        settings.save()


@storeDlgSizeDecorator
class SettingsDialog(QDialog):
    def __init__(self, collection, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self.setWindowTitle(self.tr("Settings"))

        self.tab = QTabWidget(self)
        mainPage = MainSettingsPage(collection, self)
        self.tab.addTab(mainPage, self.tr("Main"))
        if collection.isOpen():
            collectionPage = CollectionSettingsPage(collection, self)
            self.tab.addTab(collectionPage, self.tr("Collection"))
        else:
            index = self.tab.addTab(QWidget(), self.tr("Collection"))
            self.tab.setTabEnabled(index, False)
        if collection.isOpen():
            fieldsPage = FieldsSettingsPage(collection, self)
            self.tab.addTab(fieldsPage, self.tr("Fields"))
        else:
            index = self.tab.addTab(QWidget(), self.tr("Fields"))
            self.tab.setTabEnabled(index, False)
        if collection.isOpen():
            importPage = ImportSettingsPage(self)
            self.tab.addTab(importPage, self.tr("Import"))
        else:
            index = self.tab.addTab(QWidget(), self.tr("Import"))
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
            if page.isEnabled():
                page.save()

        self.accept()
