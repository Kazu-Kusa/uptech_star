import json
import os
from typing import Tuple, Dict

CONFIG_FILE: str = './config.json'
PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))
PATH_CONFIG = os.path.join(PACKAGE_ROOT, CONFIG_FILE)
with open(PATH_CONFIG, mode='r') as config_file:
    config: Dict = json.load(config_file)

FAN_GPIO_PWM: int = 18
FAN_pulse_frequency: int = 20000
FAN_duty_time_us: int = 1000000
FAN_PWN_range: int = 100

ZEROS: Tuple[int, int, int, int] = (0, 0, 0, 0)

DIR_CACHE: str = 'cache'
DIR_LID_SO: str = 'lib'

ENV_LIB_SO_PATH: str = 'LIB_SO_PATH'
ENV_CACHE_DIR_PATH: str = 'CACHE_DIR_PATH'

CONFIG_PRE_COMPILE_CMD: str = 'PRE_COMPILE_CMD'
CONFIG_DRIVER_DEBUG_MODE: str = 'DRIVER_DEBUG_MODE'
CONFIG_MOTOR_IDS: str = 'MOTOR_IDS'
CONFIG_MOTOR_DIRS: str = 'MOTOR_DIRS'
CONFIG_HANG_TIME_MAX_ERROR: str = 'HANG_TIME_MAX_ERROR'

PRE_COMPILE_CMD: bool = config.get(CONFIG_PRE_COMPILE_CMD)
DRIVER_DEBUG_MODE: bool = config.get(CONFIG_DRIVER_DEBUG_MODE)
MOTOR_IDS: Tuple[int, int, int, int] = tuple(config.get(CONFIG_MOTOR_IDS))
MOTOR_DIRS: Tuple[int, int, int, int] = tuple(config.get(CONFIG_MOTOR_DIRS))
HANG_TIME_MAX_ERROR: int = config.get(CONFIG_HANG_TIME_MAX_ERROR)

PATH_CACHE = os.path.join(PACKAGE_ROOT, DIR_CACHE)
PATH_LD = os.path.join(PACKAGE_ROOT, DIR_LID_SO)
HALT_CMD = b'v0\r'
