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

    if money == '.':
        return 0

    return float(money)
