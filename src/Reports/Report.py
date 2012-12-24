import codecs
import os
# TODO: For speedup use additional a http://pypi.python.org/pypi/MarkupSafe
from jinja2 import Environment, FileSystemLoader

from PyQt4 import QtGui, QtCore

from Tools import Gui

def copyFolder(sourceFolder, destFolder):
    sourceDir = QtCore.QDir(sourceFolder)
    if not sourceDir.exists():
        return

    destDir = QtCore.QDir(destFolder)
    if not destDir.exists():
        destDir.mkpath(destFolder)

    files = sourceDir.entryList(QtCore.QDir.Files)
    for file in files:
        srcName = sourceFolder + "/" + file
        destName = destFolder + "/" + file
        QtCore.QFile.copy(srcName, destName)

    files = sourceDir.entryList(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)
    for file in files:
        srcName = sourceFolder + "/" + file
        destName = destFolder + "/" + file
        copyFolder(srcName, destName)

def scanTemplates():
    templates = []

    sourceDir = QtCore.QDir(Report.BASE_FOLDER)
    if not sourceDir.exists():
        return templates

    files = sourceDir.entryList(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)
    for file in files:
        templates.append(file)

    return templates

class Report(QtCore.QObject):
    BASE_FOLDER = 'templates'

    def __init__(self, model, dstPath, parent=None):
        super(Report, self).__init__(parent)

        self.model = model
        self.dstPath = dstPath

    def generate(self, template_name, records, single_file=False):
        if os.path.exists('%s/%s/coin.htm' % (self.BASE_FOLDER, template_name)):
            has_item_template = True
        else:
            has_item_template = False
            single_file = True

        self.mapping = {'single_file': single_file}

        if len(records) == 1:
            static_files = "coin_%d_files" % records[0].value('id')
        else:
            static_files = "coins_files"
        self.contentDir = os.path.join(self.dstPath, static_files)

        self.mapping['static_files'] = static_files

        copyFolder('%s/%s/files' % (self.BASE_FOLDER, template_name),
                   self.contentDir)

        self.env = Environment(loader=FileSystemLoader('%s/%s' % (self.BASE_FOLDER, template_name)))

        titles_mapping = {}
        for field in self.model.fields:
            titles_mapping[field.name] = field.title
        self.mapping['titles'] = titles_mapping

        if len(records) == 1 and has_item_template:
            dstFile = self._generateItem(records[0])
        else:
            progressDlg = Gui.ProgressDialog(self.tr("Generating report"),
                            self.tr("Cancel"), len(records), self.parent())

            record_data = []
            for record in records:
                progressDlg.step()
                if progressDlg.wasCanceled():
                    return None

                if single_file:
                    record_data.append(self.__recordMapping(record))
                else:
                    self._generateItem(record)
                    record_data.append(self.mapping['record'])

            self.mapping['records'] = record_data

            template = self.env.get_template('coins.htm')
            res = template.render(self.mapping)

            dstFile = os.path.join(self.dstPath, "coins.htm")
            f = codecs.open(dstFile, 'w', 'utf-8')
            f.write(res)
            f.close()

            progressDlg.reset()

        return dstFile

    def _generateItem(self, record):
        self.mapping['record'] = self.__recordMapping(record)

        template = self.env.get_template('coin.htm')
        res = template.render(self.mapping)

        dstFile = os.path.join(self.dstPath, "coin_%d.htm" % record.value('id'))
        f = codecs.open(dstFile, 'w', 'utf-8')
        f.write(res)
        f.close()

        return dstFile

    def __recordMapping(self, record):
        imgFields = ['image', 'obverseimg', 'reverseimg',
                     'photo1', 'photo2', 'photo3', 'photo4']

        record_mapping = {}
        for field in self.model.fields:
            value = record.value(field.name)
            if value is None or value == '' or isinstance(value, QtCore.QPyNullVariant):
                record_mapping[field.name] = ''
            else:
                if field.name in imgFields:
                    if field.name == 'image':
                        ext = 'png'
                    else:
                        ext = 'jpg'

                    imgFileTitle = "%s_%d.%s" % (field.name, record.value('id'), ext)
                    imgFile = os.path.join(self.contentDir, imgFileTitle)

                    image = QtGui.QImage()
                    image.loadFromData(record.value(field.name))
                    image.save(imgFile)
                    record_mapping[field.name] = imgFileTitle
                else:
                    record_mapping[field.name] = value

        return record_mapping
