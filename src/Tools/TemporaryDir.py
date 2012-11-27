import shutil
import tempfile

__path = None
__prefix = ''


def init(prefix):
    global __prefix

    __prefix = prefix


def path():
    global __path

    if not __path:
        __path = tempfile.mkdtemp(prefix=__prefix)
        print(__path)

    return __path

def remove():
    global __path

    if __path:
        shutil.rmtree(__path, True)
        __path = None
