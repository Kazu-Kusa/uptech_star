import json
import os
from typing import Tuple, Dict

CONFIG_FILE: str = './config.json'
PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))
PATH_CONFIG = os.path.join(PACKAGE_ROOT, CONFIG_FILE)


def read_config() -> Dict:
    try:
        with open(PATH_CONFIG, mode='r') as config_file:
            config: Dict = json.load(config_file)
        return config
    except FileNotFoundError:
        raise Exception("config file not found")
    except json.JSONDecodeError:
        raise Exception("failed to decode config file")


try:
    config: Dict = read_config()
except Exception as e:
    print("failed to load config：", e)
    # 可以选择终止程序或使用默认配置
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
CONFIG_TAG_GROUP: str = 'TAG_GROUP'
CONFIG_DEFAULT_BASELINE: str = 'DEFAULT_BASELINE'
CONFIG_DEFAULT_GRAYS_BASELINE: str = 'DEFAULT_GRAYS_BASELINE'
CONFIG_DRIVER_SERIAL_PORT: str = 'DRIVER_SERIAL_PORT'

PRE_COMPILE_CMD: bool = config.get(CONFIG_PRE_COMPILE_CMD)
DRIVER_DEBUG_MODE: bool = config.get(CONFIG_DRIVER_DEBUG_MODE)
MOTOR_IDS: Tuple[int, int, int, int] = tuple(config.get(CONFIG_MOTOR_IDS))
MOTOR_DIRS: Tuple[int, int, int, int] = tuple(config.get(CONFIG_MOTOR_DIRS))
HANG_TIME_MAX_ERROR: int = config.get(CONFIG_HANG_TIME_MAX_ERROR)
TAG_GROUP: str = config.get(CONFIG_TAG_GROUP)
DEFAULT_BASELINE: int = config.get(CONFIG_DEFAULT_BASELINE)
DEFAULT_GRAYS_BASELINE: int = config.get(CONFIG_DEFAULT_GRAYS_BASELINE)
DRIVER_SERIAL_PORT: str = config.get(CONFIG_DRIVER_SERIAL_PORT)

PATH_CACHE = os.path.join(PACKAGE_ROOT, DIR_CACHE)
PATH_LD = os.path.join(PACKAGE_ROOT, DIR_LID_SO)
HALT_CMD = b'v0\r'
BREAK_ACTION_KEY = 'break_action'
BREAKER_FUNC_KEY = 'breaker_func'
ACTION_DURATION = 'action_duration'
ACTION_SPEED_KEY = 'action_speed'
HANG_DURING_ACTION_KEY = 'hang_during_action'

GRAYS_SENSOR_ID = (6, 7)
FRONT_SENSOR_ID = (1, 2)
REAR_SENSOR_ID = (0, 3)
SIDES_SENSOR_ID = (7, 8)
START_MAX_LINE = 1800
EDGE_MAX_LINE = 1750

REAR_WATCHER_NAME = 'rear_watcher'
FRONT_WATCHER_NAME = 'front_watcher'
SIDES_WATCHER_NAME = 'sides_watcher'
GRAYS_WATCHER_NAME = 'grays_watcher'
