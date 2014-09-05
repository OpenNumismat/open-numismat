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
