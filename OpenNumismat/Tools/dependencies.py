from importlib.util import find_spec

HAS_ZXING = find_spec("zxingcpp") is not None
HAS_REMBG = find_spec("rembg") is not None
