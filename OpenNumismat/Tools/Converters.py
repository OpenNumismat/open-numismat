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
            if float(string) == 0.25:
                return '¼', True
            elif float(string) == 0.33:
                return '⅓', True
            elif float(string) == 0.5:
                return '½', True
            elif float(string) == 0.75:
                return '¾', True
            elif float(string) == 1.25:
                return '1¼', True
            elif float(string) == 1.5:
                return '1½', True
            elif float(string) == 2.5:
                return '2½', True
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
