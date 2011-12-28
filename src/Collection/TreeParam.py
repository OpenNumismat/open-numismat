from PyQt4 import QtCore

class TreeParam(QtCore.QObject):
    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        
        self._params = []
    
    def init(self, model):
        self.rootTitle = model.title
        allFields = model.fields
        self._params = [allFields.type, allFields.country, allFields.period,
                        [allFields.value, allFields.unit],
                        allFields.series, allFields.year, allFields.mintmark]
    
    def params(self):
        return self._params
    
    def clear(self):
        del self._params[:]   # clearing list
    
    def append(self, field):
        self._params.append(field)
    
    def usedFields(self):
        fields = []
        for param in self._params:
            if isinstance(param, list):
                fields.extend(param)
            else:
                fields.append(param)
        
        return fields
    
    def __iter__(self):
        self.index = 0
        return self
    
    def __next__(self):
        if self.index == len(self._params):
            raise StopIteration
        self.index = self.index + 1
        return self._params[self.index-1]
