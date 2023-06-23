import os
import warnings

libdir = os.path.abspath(os.path.dirname(__file__))
os.environ['LIB_SO_PATH'] = os.path.join(libdir, 'lib')

from .module import *

try:
    import cv2, numpy
    from .module.utils import *
except:
    warnings.warn("utils import failed")
try:
    from .module.hotConfigure.valueTest import *
    from .module.hotConfigure.status import *
except:
    pass
__version__ = "0.7"
__all__ = {
    'module',
    'extension'
}
