import codecs
import csv
import html
import sys

exportToExcelAvailable = True

try:
    import xlwt
except ImportError:
    print('xlwt module missed. Exporting to Excel not available')
exportToExcelAvailable = False


class __ExportBase():
    def __init__(self, fileName, title=''):
        self.fileName = fileName
        self.title = title
        self.currentRow = 0

    def open(self):
        pass

    def close(self):
        pass

    def writeHeader(self, headers):
        pass

    def writeRow(self, row):
        pass


class ExportToExcel(__ExportBase):
    def __init__(self, fileName, title=''):
        super(ExportToExcel, self).__init__(fileName, title)

    @staticmethod
    def isAvailable():
        return exportToExcelAvailable

    def open(self):
        self._wb = xlwt.Workbook()
        self._ws = self._wb.add_sheet(self.title)

    def close(self):
        self._wb.save(self.fileName)

    def writeHeader(self, headers):
        for i, val in enumerate(headers):
            self._ws.write(0, i, val)

        self.currentRow = self.currentRow + 1

    def writeRow(self, row):
        for i, val in enumerate(row):
            self._ws.write(self.currentRow, i, val)

        self.currentRow = self.currentRow + 1


class ExportToHtml(__ExportBase):
    def __init__(self, fileName, title=''):
        super(ExportToHtml, self).__init__(fileName, title)

    def open(self):
        self._file = codecs.open(self.fileName, 'w', 'utf-8')
        self._file.truncate()
        self._file.write("""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<title>""" + self.title + """</title>
<style>
td {
margin: 0;
padding: 0;
}
html, body {
font-size: 1em;
}
table {
font-family: Verdana,Helvetica;
font-size: 10px;
border: 1px solid #bbb;
border-collapse: collapse;
}
th {
background: #ddd;
}
td {
background: #ecf0f6;
}
</style>
</head>
<body>
<table border="1">
""")

    def close(self):
        self._file.write("</tbody></table></body></html>")
        self._file.close()

    def writeHeader(self, headers):
        self._file.write("<thead><tr>")
        for val in headers:
            self._file.write("<th>")
            self._file.write(html.escape(val))
            self._file.write("</th>")

        self._file.write("</tr></thead>\n")

    def writeRow(self, row):
        self._file.write("<tr>")
        for val in row:
            self._file.write("<td>")
            self._file.write(html.escape(str(val)))
            self._file.write("</td>")

        self._file.write("</tr>\n")


class ExportToCsv(__ExportBase):
    def __init__(self, fileName, title):
        super(ExportToCsv, self).__init__(fileName)

    def open(self):
        self._file = open(self.fileName, 'w', newline='')
        self._file.truncate()
        self._writer = csv.writer(self._file, delimiter=';')

    def close(self):
        self._file.close()

    def writeHeader(self, headers):
        encoded_vals = []
        for val in headers:
            value = __prepareStr(val)
            encoded_vals.append(value)

        self._writer.writerow(encoded_vals)

    def writeRow(self, row):
        encoded_vals = []
        for val in row:
            value = __prepareStr(str(val))
            encoded_vals.append(value)

        self._writer.writerow(encoded_vals)


class ExportToCsvUtf8(__ExportBase):
    def __init__(self, fileName, title=''):
        super(ExportToCsvUtf8, self).__init__(fileName)

    def open(self):
        self._file = open(self.fileName, 'w', newline='', encoding='utf-8')
        self._file.truncate()
        self._writer = csv.writer(self._file, delimiter=';')

    def close(self):
        self._file.close()

    def writeHeader(self, headers):
        self._writer.writerow(headers)

    def writeRow(self, row):
        self._writer.writerow(row)


# Prepare string for default system encoding (remove or replace extra
# characters)
def __prepareStr(string):
    encoded_str = string.encode(encoding=sys.stdout.encoding, errors='ignore')
    decoded_str = encoded_str.decode(sys.stdout.encoding)
    return decoded_str
