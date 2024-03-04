def parseBarcode(barcode):
    if len(barcode) == 20 or len(barcode) == 18:  # NGC
        return f"{barcode[-10:-3]}-{barcode[-3:]}"
    elif len(barcode) == 22:  # PCGS
        return barcode[-9:]
    elif len(barcode) == 16:  # old PCGS
        return barcode[-8:]
    else:
        return barcode
