# -*- coding: utf-8 -*-

import locale

def stringToMoney(string):
    valueBegan = False
    money = ''
    for c in string:
        if c in '0123456789':
            money = money + c
            valueBegan = True
        elif c in '.,':
            money = money + '.'
        elif c in ' \t\n\r':
            continue
        else:
            if valueBegan:
                break

    return float(money)

class FractionTypes():
    Decimal = 0
    Vulgar = 1
    VulgarUnicode = 2

def localizeMoney(value, fractionType=FractionTypes.Decimal):
    dp = locale.localeconv()['decimal_point']
    baseFractions = {
            '04': '1/25', '05': '1/20', '06': '1/15', '07': '1/15',
            '10': '1/10', '12': '1/8', '13': '1/8', '16': '1/6',
            '17': '1/6', '20': '1/5', '25': '1/4', '33': '1/3',
            '37': '3/8', '38': '3/8', '40': '2/5','50': '1/2',
            '60': '3/5', '62': '5/8', '63': '5/8', '66': '2/3',
            '67': '2/3', '75': '3/4', '80': '4/5', '83': '5/6', 
            '87': '7/8', '88': '7/8'
    }
    unicodeFractions = {
            '04': '1/25', '05': '1/20', '06': '1/15', '07': '1/15',
            '10': '1/10', '12': '⅛', '13': '⅛', '16': '⅙',
            '17': '⅙', '20': '⅕', '25': '¼', '33': '⅓',
            '37': '⅜', '38': '⅜', '40': '⅖','50': '½',
            '60': '⅗', '62': '⅝', '63': '⅝', '66': '⅔',
            '67': '⅔', '75': '¾', '80': '⅘', '83': '⅚', 
            '87': '⅞', '88': '⅞'
    }

    if fractionType == FractionTypes.Decimal:
        text = locale.format("%.2f", float(value), grouping=True)
        text = text.rstrip('0').rstrip(dp)
    else:
        if fractionType == FractionTypes.VulgarUnicode:
            fractions = unicodeFractions
        else:
            fractions = baseFractions
        
        text = "{:.2f}".format(float(value))
        integral, fraction = text.split('.')

        if fraction in fractions:
            fraction = fractions[fraction]
        else:
            text = dp.join([integral, fraction])
            text = text.rstrip('0').rstrip(dp)
            return text
        
        if integral == '0':
            text = fraction
        else:
            text = ' '.join([integral, fraction])
    
    return text

def valueToFloat(value):
    # First, get rid of the grouping
    ts = locale.localeconv()['thousands_sep']
    if ts:
        value = value.replace(ts, '')
        if ts == chr(0xA0):
            value = value.replace(' ', '')
    # next, replace the decimal point with a dot
    dp = locale.localeconv()['decimal_point']
    if dp:
        value = value.replace(dp, '.')
    
    return value

def volgarToFloat(value):
    if '.' in value:
        val = float(valueToFloat(value))
    elif '/' in value:
        # a b/c
        parts = value.split()
        if len(parts) == 1:
            a = 0
            fraction = value
        elif len(parts) == 2:
            a = parts[0]
            fraction = parts[1]
        else:
            raise ValueError
    
        b, c = fraction.split('/')
        if c == '' or b == '':
            return None
        val = float(a) + float(b)/float(c)
    else:
        fractions = {'⅛': '13', '⅙': '17', '⅕': '20', '¼': '25', '⅓': '33',
                     '⅜': '38', '⅖': '40', '½': '50', '⅗': '60', '⅝': '63',
                     '⅔': '67', '¾': '75', '⅘': '80', '⅚': '83', '⅞': '88'}
        if value[-1] in fractions:
            fraction = fractions[value[-1]]
            integer = value[:-1].strip()
            val = float('.'.join([integer, fraction]))
        else:
            val = float(valueToFloat(value))
    
    return val
