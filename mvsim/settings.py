# flake8: noqa
from mvsim.settings_shared import *

try:
    from mvsim.local_settings import *
except ImportError:
    pass
