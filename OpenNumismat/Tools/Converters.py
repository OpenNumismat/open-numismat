# -*- coding: utf-8 -*-

from PySide6.QtGui import QTextDocument
from PySide6.QtCore import QLocale


def stringToMoney(string):
    spaces = ' \t\n\r' + QLocale.system().groupSeparator()
    dp = [QLocale.system().decimalPoint(), ]
    if dp[0] == ',' and '.' != QLocale.system().groupSeparator():
        dp.append('.')

    value_began = False
    money = '0'
    for c in string:
        if c in '0123456789':
            money = money + c
            value_began = True
        elif c == '-' and not value_began:
            money = '-0'
        elif c in dp:
            money += '.'
        elif c in spaces:
            continue
        else:
            if value_began:
                break

    try:
        return float(money)
    except ValueError:
        return 0.


def numberWithFraction(string, enabled=True):
    if enabled:
        try:
            value = float(string)
            if value == 0.02:
                return '1⁄48', True
            elif value == 0.04:
                return '1⁄24', True
            elif value == 0.05:
                return '1⁄20', True
            elif value == 0.06:
                return '1⁄16', True
            elif value == 0.08:
                return '1⁄12', True
            elif value == 0.1:
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
            elif value == 4.5:
                return '4½', True
            elif value == 7.5:
                return '7½', True
            elif value == 12.5:
                return '12½', True
        except (ValueError, TypeError):
            pass

    return string, False


def numberToFraction(text):
    if text == '⅟48' or text == '1⁄48' or text == '1/48':
        text = '0.02'
    elif text == '⅟24' or text == '1⁄24' or text == '1/24':
        text = '0.04'
    elif text == '⅟20' or text == '1⁄20' or text == '1/20':
        text = '0.05'
    elif text == '⅟16' or text == '1⁄16' or text == '1/16':
        text = '0.06'
    elif text == '⅟12' or text == '1⁄12' or text == '1/12':
        text = '0.08'
    elif text == '⅒'  or text == '1/10':
        text = '0.1'
    elif text == '⅛' or text == '1/8':
        text = '0.12'
    elif text == '⅙' or text == '1/6':
        text = '0.16'
    elif text == '⅕' or text == '1/5':
        text = '0.2'
    elif text == '¼' or text == '1/4':
        text = '0.25'
    elif text == '⅓' or text == '1/3':
        text = '0.33'
    elif text == '½' or text == '1/2':
        text = '0.5'
    elif text == '⅔' or text == '2/3':
        text = '0.66'
    elif text == '¾' or text == '3/4':
        text = '0.75'
    elif text == '1¼':
        text = '1.25'
    elif text == '1½':
        text = '1.5'
    elif text == '2½':
        text = '2.5'
    elif text == '4½':
        text = '4.5'
    elif text == '7½':
        text = '7.5'
    elif text == '12½':
        text = '12.5'
    return text


def htmlToPlainText(text):
    RICH_PREFIX = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" '\
                  '"http://www.w3.org/TR/REC-html40/strict.dtd">'
    if text.startswith(RICH_PREFIX):
        document = QTextDocument()
        document.setHtml(text)
        text = document.toPlainText()

    return text


def _compareYearStrings(left, right):
    if left and left[0] == '-' and right and right[0] == '-':
        left_year = 0
        right_year = 0
        for c in left[1:]:
            if c.isdigit():
                left_year = left_year * 10 + (ord(c) - ord('0'))
            else:
                break
        for c in right[1:]:
            if c.isdigit():
                right_year = right_year * 10 + (ord(c) - ord('0'))
            else:
                break

        if left_year != right_year:
            # Invert comparing for negative years
            return -(left_year - right_year)

    if left < right:
        return -1
    # elif left == right:
    #    return 0
    else:
        return 1


def compareYears(left, right):
    if isinstance(left, str):
        right = str(right)
        return _compareYearStrings(left, right)
    elif isinstance(right, str):
        left = str(left)
        return _compareYearStrings(left, right)

    return left - right
