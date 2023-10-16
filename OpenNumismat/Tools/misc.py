def versiontuple(v):
    try:
        return tuple(map(int, (v.split("."))))
    except:
        return tuple((99, 99, 99))  # It is a beta version and newer
