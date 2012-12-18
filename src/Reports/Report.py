import codecs
import os
import shutil
# TODO: For speedup use additional a http://pypi.python.org/pypi/MarkupSafe
from jinja2 import Environment, FileSystemLoader

from PyQt4 import QtGui, QtCore

class Report(QtCore.QObject):
    def __init__(self, model, dstPath, parent=None):
        super(Report, self).__init__(parent)

        self.model = model
        self.dstPath = dstPath

    def generate(self, records, single_file=False):
        self.single_file = single_file
        self.mapping = {'single_file': single_file}

        if len(records) > 1:
            static_files = "coins_files"
        else:
            static_files = "coin_%d_files" % records[0].value('id')
        self.contentDir = os.path.join(self.dstPath, static_files)

        self.mapping['static_files'] = static_files

        shutil.rmtree(self.contentDir, ignore_errors=True)
        shutil.copytree('templates/cbr/files', self.contentDir)

        self.env = Environment(loader=FileSystemLoader('templates/cbr'))

        titles_mapping = {}
        for field in self.model.fields:
            titles_mapping[field.name] = field.title
        self.mapping['titles'] = titles_mapping

        if len(records) > 1:
            record_data = []
            for record in records:
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
        else:
            dstFile = self._generateItem(records[0])

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
            if record.value(field.name):
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
                    record_mapping[field.name] = record.value(field.name)
            else:
                record_mapping[field.name] = ''

        return record_mapping
