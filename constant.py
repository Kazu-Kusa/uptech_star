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
CONFIG_MOTOR_ID_LIST: str = 'MOTOR_ID_LIST'

PRE_COMPILE_CMD: bool = config.get(CONFIG_PRE_COMPILE_CMD)
MOTOR_ID_LIST: Tuple[int, int, int, int] = tuple(config.get(CONFIG_MOTOR_ID_LIST))

PATH_CACHE = os.path.join(PACKAGE_ROOT, DIR_CACHE)
PATH_LD = os.path.join(PACKAGE_ROOT, DIR_LID_SO)
HALT_CMD = b'v0\r'