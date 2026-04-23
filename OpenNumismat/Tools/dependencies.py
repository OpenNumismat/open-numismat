from importlib.util import find_spec

HAS_ZXING = find_spec("zxingcpp") is not None
HAS_REMBG = find_spec("rembg") is not None

try:
    from OpenNumismat.private_keys import FINANCE_PROXY
except ImportError:
    print('Finance Service not available')
    FINANCE_AVAILABLE = False
else:
    FINANCE_AVAILABLE = True
