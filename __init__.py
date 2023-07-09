import warnings

from .constant import ENV_LIB_SO_PATH, ENV_CACHE_DIR_PATH, PATH_CACHE, PATH_LD
from .module.db_tools import set_env_var

set_env_var(ENV_CACHE_DIR_PATH, PATH_CACHE)
set_env_var(ENV_LIB_SO_PATH, PATH_LD)

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
__version__ = "0.8"
__all__ = {
    'module',
    'extension'
}
