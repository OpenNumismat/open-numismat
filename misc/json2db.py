import json
import os
from pathlib import Path

from PySide6.QtCore import QLocale, QTranslator
from PySide6.QtWidgets import QApplication

from OpenNumismat import resources
from OpenNumismat.Collection.Collection import Collection
from OpenNumismat.Collection.CollectionFields import ImageFields
from OpenNumismat.Reference.Reference import Reference

src_dir = os.path.join(os.path.dirname(__file__), "../tools/db")
dst_dir = os.path.join(os.path.dirname(__file__), "../OpenNumismat/db")

app = QApplication([])

for filename in os.listdir(src_dir):
    _, file_extension = os.path.splitext(filename)
    if file_extension == ".json":
        json_file_name = os.path.join(src_dir, filename)
        with open(json_file_name, 'r', encoding='utf-8') as file:
            data = json.load(file)

        file_title = filename[:-5]
        lang = file_title.split('_')[-1]
        translator = QTranslator(app)
        if translator.load(QLocale(lang), 'lang', '_', ':/i18n'):
            app.installTranslator(translator)

        dst_file_name = os.path.join(dst_dir, f"demo_{lang}.db")
        Path(dst_file_name).unlink(missing_ok=True)

        collection = Collection()
        collection.create(dst_file_name)
        collection.reference = Reference(collection.fields)

        model = collection.model()

        for coin in data['coins']:
            record = model.record()
            for field, value in coin.items():
                if field in ImageFields:
                    image_file_name = os.path.join(src_dir, f"demo_images/{value}")
                    with open(image_file_name, 'rb') as file:
                        image = file.read()
                    record.setValue(field, image)
                else:
                    record.setValue(field, value)

            model.appendRecord(record)
