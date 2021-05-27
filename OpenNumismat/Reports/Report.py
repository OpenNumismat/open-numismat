import codecs
import os

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print('jinja2 module missed. Report engine not available')

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage

from OpenNumismat.Tools import Gui
import OpenNumismat


def copyFolder(sourceFolder, destFolder):
    sourceDir = QtCore.QDir(sourceFolder)
    if not sourceDir.exists():
        return

    destDir = QtCore.QDir(destFolder)
    if not destDir.exists():
        destDir.mkpath(destFolder)

    files = sourceDir.entryList(QtCore.QDir.Files)
    for file in files:
        srcName = os.path.join(sourceFolder, file)
        destName = os.path.join(destFolder, file)
        QtCore.QFile.remove(destName)  # remove if existing
        QtCore.QFile.copy(srcName, destName)

    files = sourceDir.entryList(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)
    for file in files:
        srcName = os.path.join(sourceFolder, file)
        destName = os.path.join(destFolder, file)
        copyFolder(srcName, destName)


def scanTemplates():
    templates = []

    path = os.path.join(OpenNumismat.HOME_PATH, 'templates')
    sourceDir = QtCore.QDir(path)
    if sourceDir.exists():
        files = sourceDir.entryList(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)
        for file in files:
            templates.append((file, os.path.join(path, file)))

    path = os.path.join(OpenNumismat.PRJ_PATH, 'templates')
    sourceDir = QtCore.QDir(path)
    if sourceDir.exists():
        files = sourceDir.entryList(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)
        for file in files:
            templates.append((file, os.path.join(path, file)))

    return templates


class Report(QtCore.QObject):
    def __init__(self, model, template, dstPath, parent=None):
        super().__init__(parent)

        self.model = model
        self.srcFolder = template

        fileInfo = QtCore.QFileInfo(dstPath)
        if fileInfo.exists() and fileInfo.isDir():
            self.dstFolder = dstPath
            self.fileName = None
        else:
            self.dstFolder = fileInfo.dir().path()
            self.fileName = fileInfo.fileName()

    def generate(self, indexes, single_file=False):
        if os.path.exists(os.path.join(self.srcFolder, 'coin.htm')):
            has_item_template = True
        else:
            has_item_template = False
            single_file = True

        self.mapping = {'single_file': single_file,
                        'date': QtCore.QDate.currentDate().toString(QtCore.Qt.DefaultLocaleLongDate)}

        self.mapping['collection'] = {'title': self.model.description.title,
                            'description': self.model.description.description,
                            'author': self.model.description.author}

        if not self.fileName:
            if len(indexes) == 1 and has_item_template:
                self.fileName = "coin_%d.htm" % self.__getId(indexes[0])
            else:
                self.fileName = "coins.htm"
        static_files = QtCore.QFileInfo(self.fileName).baseName() + '_files'
        self.contentDir = os.path.join(self.dstFolder, static_files)

        self.mapping['static_files'] = static_files

        copyFolder(os.path.join(self.srcFolder, 'files'), self.contentDir)

        loader = FileSystemLoader(self.srcFolder)
        self.env = Environment(loader=loader, autoescape=True)

        titles_mapping = {}
        for field in self.model.fields:
            titles_mapping[field.name] = field.title
        self.mapping['titles'] = titles_mapping

        if len(indexes) == 1 and has_item_template:
            self.mapping['record'] = self.__recordMapping(indexes[0])
            dstFile = self.__render('coin.htm', self.fileName)
        else:
            progressDlg = Gui.ProgressDialog(self.tr("Generating report"),
                            self.tr("Cancel"), len(indexes), self.parent())

            record_data = []
            for index in indexes:
                progressDlg.step()
                if progressDlg.wasCanceled():
                    return None

                recordMapping = self.__recordMapping(index)
                record_data.append(recordMapping)
                if not single_file:
                    self.mapping['record'] = recordMapping
                    self.__render('coin.htm', "coin_%d.htm" % self.__getId(index))

            self.mapping['records'] = record_data

            dstFile = self.__render('coins.htm', self.fileName)

            progressDlg.reset()

        return dstFile

    def __render(self, template, fileName):
        template = self.env.get_template(template)
        res = template.render(self.mapping)

        dstFile = os.path.join(self.dstFolder, fileName)
        f = codecs.open(dstFile, 'w', 'utf-8')
        f.write(res)
        f.close()

        return dstFile

    def __getId(self, index):
        field_index = self.model.index(index.row(), self.model.fieldIndex('id'))
        return self.model.data(field_index, Qt.UserRole)

    def __recordMapping_new(self, index):
        record = CollectionRecord(self.model, index.row())
        record.contentDir = self.contentDir
        return record

    def __recordMapping(self, index):
        imgFields = ('image', 'obverseimg', 'reverseimg', 'edgeimg',
                     'varietyimg', 'photo1', 'photo2', 'photo3', 'photo4',
                     'photo5', 'photo6', 'signatureimg')

        record_mapping = {}
        record_mapping['status_raw'] = ''
        record_mapping['issuedate_raw'] = ''
        row = index.row()
        for field in self.model.fields:
            field_index = self.model.index(row, self.model.fieldIndex(field.name))
            value = self.model.data(field_index, Qt.DisplayRole)

            if value is None or value == '':
                record_mapping[field.name] = ''
            else:
                if field.name in imgFields:
                    if field.name == 'image':
                        ext = 'png'
                    else:
                        ext = 'jpg'

                    imgFileTitle = "%s_%d.%s" % (field.name, self.__getId(index), ext)
                    imgFile = os.path.join(self.contentDir, imgFileTitle)

                    image = QImage()
                    image.loadFromData(value)
                    image.save(imgFile)
                    record_mapping[field.name] = imgFileTitle
                else:
                    record_mapping[field.name] = value
                    if field.name == 'status':
                        record_mapping['status_raw'] = self.model.data(field_index, Qt.UserRole)
                    elif field.name == 'issuedate':
                        record_mapping['issuedate_raw'] = self.model.data(field_index, Qt.UserRole)

        return record_mapping


class CollectionRecord(dict):
    imgFields = ('image', 'obverseimg', 'reverseimg', 'edgeimg', 'varietyimg',
                 'photo1', 'photo2', 'photo3', 'photo4', 'photo5', 'photo6',
                 'signatureimg')

    def __init__(self, model, row):
        self.model = model
        self.row = row
        self.data = {}

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]

        if key[-4:] == '_raw':
            index = self.model.index(self.row, self.model.fieldIndex(key[:-4]))
            value = self.model.data(index, Qt.UserRole)
        else:
            index = self.model.index(self.row, self.model.fieldIndex(key))
            value = self.model.data(index, Qt.DisplayRole)

        if value is None or value == '':
            self.data[key] = ''
            return ''
        elif key in CollectionRecord.imgFields:
            if key == 'image':
                ext = 'png'
            else:
                ext = 'jpg'

            field_index = self.model.index(self.row, self.model.fieldIndex('id'))
            id_ = self.model.data(field_index, Qt.UserRole)
            imgFileTitle = "%s_%d.%s" % (key, id_, ext)
            imgFile = os.path.join(self.contentDir, imgFileTitle)

            image = QImage()
            image.loadFromData(value)
#            size = 500
#            if image.width() > size or image.height() > size:
#                image = image.scaled(size, size,
#                        Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image.save(imgFile)
            self.data[key] = imgFileTitle
            return imgFileTitle
        else:
            self.data[key] = value
            return value

