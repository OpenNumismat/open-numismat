# -*- coding: utf-8 -*-

from PyQt5.QtGui import QTextDocument


def stringToMoney(string):
    value_began = False
    money = '0'
    for c in string:
        if c in '0123456789':
            money = money + c
            value_began = True
        elif c == '-' and not value_began:
            money = '-0'
        elif c in '.,':
            money += '.'
        elif c in ' \t\n\r':
            continue
        else:
            if value_began:
                break

    return float(money)


def numberWithFraction(string, enabled=True):
    if enabled:
        try:
            value = float(string)
            if value == 0.1:
                return '⅒', True
            elif value == 0.12:
                return '⅛', True
            elif value == 0.16:
                return '⅙', True
            elif value == 0.2:
                return '⅕', True
            elif value == 0.25:
                return '¼', True
            elif value == 0.33:
                return '⅓', True
            elif value == 0.5:
                return '½', True
            elif value == 0.66:
                return '⅔', True
            elif value == 0.75:
                return '¾', True
            elif value == 1.25:
                return '1¼', True
            elif value == 1.5:
                return '1½', True
            elif value == 2.5:
                return '2½', True
            elif value == 7.5:
                return '7½', True
            elif value == 12.5:
                return '12½', True
        except (ValueError, TypeError):
            pass

    return string, False


def htmlToPlainText(text):
    RICH_PREFIX = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" '\
                  '"http://www.w3.org/TR/REC-html40/strict.dtd">'
    if text.startswith(RICH_PREFIX):
        document = QTextDocument()
        document.setHtml(text)
        text = document.toPlainText()

    return text
