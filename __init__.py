import os
import warnings

from repo.uptechStar.constant import CONFIG_FILE, DIR_CACHE, DIR_LID_SO, ENV_LIB_SO_PATH, ENV_CACHE_DIR_PATH, \
    PACKAGE_ROOT, PATH_CACHE, PATH_LD
from .constant import PATH_CACHE, PATH_LD
from .module.db_tools import makedirs

os.environ[ENV_LIB_SO_PATH]: str = PATH_LD
makedirs(PATH_LD)

os.environ[ENV_CACHE_DIR_PATH]: str = PATH_CACHE
makedirs(PATH_CACHE)

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
