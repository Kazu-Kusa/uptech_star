import warnings

from .module import *

try:
    import cv2, numpy
    from .module.utils import *
except ImportError:
    warnings.warn("utils import failed")
try:
    from .module.hotConfigure.valueTest import *
    from .module.hotConfigure.status import *
    from .module.hotConfigure.sync_test import *
except ImportError:
    warnings.warn("hotConfigure import failed")
__version__ = "1.1.dev0"
__all__ = {
    'module',
    'extension'
}
