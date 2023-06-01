import os
import sys

sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./hotConfigure'))
libdir = os.path.abspath(os.path.dirname(__file__))
os.environ['LIB_SO_PATH'] = os.path.join(libdir, 'lib')

from .module.uptech import *
from .module.up_controller import *
from .module.serial_helper import *
from .module.close_loop_controller import *
from .module.timer import *
from .module.pid import *
from .module.algrithm_tools import *

try:
    from .module.utils import *
except ImportError:
    warnings.warn('failed to import utils')

from .module.hotConfigure.valueTest import *
from .module.hotConfigure.status import *

__version__ = "0.4"
__all__ = {
    'module',
    'extension'
}
