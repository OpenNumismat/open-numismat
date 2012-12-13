import codecs
import os
import shutil
# TODO: For speedup use additional a http://pypi.python.org/pypi/MarkupSafe
from jinja2 import Environment, FileSystemLoader

from PyQt4 import QtGui, QtCore

from Collection.CollectionFields import CollectionFields

class Report(QtCore.QObject):
    def __init__(self, model, dstPath, parent=None):
        super(Report, self).__init__(parent)

        self.model = model
        self.dstPath = dstPath

    def generate(self, records):
        self.mapping = {}

        if len(records) > 1:
            static_files = "coins_files"
        else:
            static_files = "coin_%d_files" % records[0].value('id')
        self.contentDir = os.path.join(self.dstPath, static_files)

        self.mapping['static_files'] = static_files

        shutil.rmtree(self.contentDir, ignore_errors=True)
        shutil.copytree('templates/cbr/files', self.contentDir)

        self.env = Environment(loader=FileSystemLoader('templates/cbr'))

        if len(records) > 1:
            record_data = []
            for record in records:
                self._generateItem(record)
                record_data.append(self.mapping.copy())

            template = self.env.get_template('coins.htm')
            res = template.render({'records': record_data, 'static_files': static_files})

            dstFile = os.path.join(self.dstPath, "coins.htm")
            f = codecs.open(dstFile, 'w', 'utf-8')
            f.write(res)
            f.close()
        else:
            dstFile = self._generateItem(records[0])

        return dstFile

    def _generateItem(self, record):
        imgFields = ['image', 'obverseimg', 'reverseimg',
                     'photo1', 'photo2', 'photo3', 'photo4']

        for field in self.model.fields:
            self.mapping[field.name + '_title'] = field.title
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
                    self.mapping[field.name] = imgFileTitle
                else:
                    self.mapping[field.name] = record.value(field.name)
            else:
                self.mapping[field.name] = ''

        template = self.env.get_template('coin.htm')
        res = template.render(self.mapping)

        dstFile = os.path.join(self.dstPath, "coin_%d.htm" % record.value('id'))
        f = codecs.open(dstFile, 'w', 'utf-8')
        f.write(res)
        f.close()

        return dstFile
