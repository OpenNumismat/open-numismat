from PyQt4 import QtCore

class TreeParam(QtCore.QObject):
    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        
        self._params = []
    
    def init(self, model):
        self.rootTitle = model.title
        allFields = model.fields
        self._params = [[allFields.type,], [allFields.country,], [allFields.period,],
                        [allFields.value, allFields.unit],
                        [allFields.series,], [allFields.year,], [allFields.mintmark,]]
    
    def params(self):
        return self._params
    
    def clear(self):
        del self._params[:]   # clearing list
    
    def append(self, fields):
        if not isinstance(fields, list):
            fields = [fields,]
        
        self._params.append(fields)
    
    def usedFieldNames(self):
        names = []
        for param in self._params:
            names.extend([field.name for field in param])
        
        return names
    
    def __iter__(self):
        self.index = 0
        return self
    
    def __next__(self):
        if self.index == len(self._params):
            raise StopIteration
        self.index = self.index + 1
        return self._params[self.index-1]
