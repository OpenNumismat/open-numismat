import os
import sys

from OpenNumismat.main import main


PRJ_PATH = os.path.abspath(os.path.dirname(__file__))
# sys.frozen is True when running from cx_Freeze executable
if getattr(sys, 'frozen', False):
    PRJ_PATH = os.path.dirname(sys.executable)

__all__ = ["main"]
