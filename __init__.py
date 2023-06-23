import os
import warnings

from .module.constant import CACHE_DIR, LID_SO_DIR, ENV_LIB_SO_PATH, ENV_CACHE_DIR_PATH


def makedirs(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


base_dir = os.path.abspath(os.path.dirname(__file__))
ld_path = os.path.join(base_dir, LID_SO_DIR)
os.environ[ENV_LIB_SO_PATH] = ld_path
makedirs(ld_path)

cache_path = os.path.join(base_dir, CACHE_DIR)
os.environ[ENV_CACHE_DIR_PATH] = cache_path
makedirs(cache_path)

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
