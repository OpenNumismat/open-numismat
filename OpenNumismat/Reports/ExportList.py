import codecs
import csv
import io
import html
import openpyxl
from PIL import Image

from PySide6.QtCore import QByteArray


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

    def acceptImages(self):
        return False


class ExportToExcel(__ExportBase):

    def open(self):
        self._wb = openpyxl.Workbook()
        self._ws = self._wb.active
        self._ws.title = self.title

        self._current_row = 1

    def close(self):
        self._wb.save(self.fileName)

    def writeHeader(self, headers):
        self._ws.append(headers)

    def writeRow(self, row):
        for i, item in enumerate(row):
            if isinstance(item, QByteArray):
                image_data = item.data()
                image = Image.open(io.BytesIO(image_data))
                img = openpyxl.drawing.image.Image(image)

                cell = self._ws.cell(self._current_row + 1, i + 1)
                self._ws.add_image(img, cell.coordinate)

                row[i] = None

        self._ws.append(row)

        self._current_row += 1

    def acceptImages(self):
        return True


class ExportToHtml(__ExportBase):

    def open(self):
        self._file = codecs.open(self.fileName, 'w', 'utf-8')
        self._file.truncate()
        self._file.write("""
<!DOCTYPE html>
<html>
<head>
<meta charset=utf-8">
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

        self._file.write("</tr></thead>\n<tbody>")

    def writeRow(self, row):
        self._file.write("<tr>")
        for val in row:
            self._file.write("<td>")
            self._file.write(html.escape(str(val)))
            self._file.write("</td>")

        self._file.write("</tr>\n")


class ExportToCsv(__ExportBase):

    def open(self):
        self._file = open(self.fileName, 'w', newline='')
        self._encoding = self._file.encoding
        self._file.truncate()
        self._writer = csv.writer(self._file, delimiter=';')

    def close(self):
        self._file.close()

    def writeHeader(self, headers):
        encoded_vals = []
        for val in headers:
            value = self.__prepareStr(val)
            encoded_vals.append(value)

        self._writer.writerow(encoded_vals)

    def writeRow(self, row):
        encoded_vals = []
        for val in row:
            value = self.__prepareStr(str(val))
            encoded_vals.append(value)

        self._writer.writerow(encoded_vals)

    # Prepare string for default system encoding (remove or replace extra
    # characters)
    def __prepareStr(self, string):
        encoded_str = string.encode(encoding=self._encoding, errors='ignore')
        decoded_str = encoded_str.decode(self._encoding)
        return decoded_str


class ExportToCsvUtf8(__ExportBase):

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
