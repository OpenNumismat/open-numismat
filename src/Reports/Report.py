import codecs
import os
import shutil
# TODO: For speedup use additional a http://pypi.python.org/pypi/MarkupSafe
from jinja2 import Environment, FileSystemLoader

from PyQt4 import QtGui, QtCore

from Collection.CollectionFields import CollectionFields

class Report(QtCore.QObject):
    def __init__(self, dstPath, parent=None):
        super(Report, self).__init__(parent)

        self.dstPath = dstPath

    def generate(self, record):
        mapping = {}

        contentDir = os.path.join(self.dstPath, "coin_%d" % record.value('id'))
        mapping['static_files'] = contentDir

        shutil.rmtree(contentDir, ignore_errors=True)
        shutil.copytree('templates/cbr/files', contentDir)

        imgFields = ['image', 'obverseimg', 'reverseimg',
                     'photo1', 'photo2', 'photo3', 'photo4']

        for field in CollectionFields():
            mapping[field.name + '_title'] = field.title
            if record.value(field.name):
                if field.name in imgFields:
                    if field.name == 'image':
                        ext = 'png'
                    else:
                        ext = 'jpg'

                    imgFileTitle = "%s.%s" % (field.name, ext)
                    imgFile = os.path.join(contentDir, imgFileTitle)

                    image = QtGui.QImage()
                    image.loadFromData(record.value(field.name))
                    image.save(imgFile)
                    mapping[field.name] = imgFileTitle
                else:
                    mapping[field.name] = record.value(field.name)
            else:
                mapping[field.name] = ''

        env = Environment(loader=FileSystemLoader('templates/cbr'))
        template = env.get_template('coin.htm')
        res = template.render(mapping)

        dstFile = os.path.join(self.dstPath, "coin_%d.htm" % record.value('id'))
        f = codecs.open(dstFile, 'w', 'utf-8')
        f.write(res)
        f.close()

        return dstFile
