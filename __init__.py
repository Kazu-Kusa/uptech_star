import os
import sys

sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./hotConfigure'))

# 设置运行环境变量LD_LIBRARY_PATH，添加lib库搜索路径
libdir = os.path.abspath(os.path.dirname(__file__))
os.environ['LD_LIBRARY_PATH'] = os.path.join(libdir, 'lib')

from .uptech import *
from .up_controller import *
from .serial_helper import *
from .close_loop_controller import *
from .hotConfigure.valueTest import *

__version__ = "1.0"
__all__ = [
    'uptech',
    'up_controller',
    'serial_helper',
    'close_loop_controller',
    'hotConfigure'
]
