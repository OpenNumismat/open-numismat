# -*- coding: utf-8 -*-


def stringToMoney(string):
    value_began = False
    money = ''
    for c in string:
        if c in '0123456789':
            money = money + c
            value_began = True
        elif c in '.,':
            money += '.'
        elif c in ' \t\n\r':
            continue
        else:
            if value_began:
                break

    if money == '.' or not money:
        return 0

    return float(money)


def numberWithFraction(string, enabled=True):
    if enabled:
        try:
            if float(string) == 0.25:
                return '¼', True
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
