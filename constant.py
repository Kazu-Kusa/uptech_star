import json
import os
from typing import Tuple, Dict

CONFIG_FILE: str = './config.json'
PACKAGE_ROOT: str = os.path.abspath(os.path.dirname(__file__))
PATH_CONFIG: str = os.path.join(PACKAGE_ROOT, CONFIG_FILE)


def read_config() -> Dict:
    try:
        with open(PATH_CONFIG, mode='r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        print(f"Config file not found at: {PATH_CONFIG}")
        return {}
    except json.decoder.JSONDecodeError:
        print(f"Invalid config file at: {PATH_CONFIG}")
        return {}


config: Dict = read_config()

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
CONFIG_DEFAULT_EDGE_BASELINE: str = 'DEFAULT_EDGE_BASELINE'
CONFIG_DEFAULT_NORMAL_BASELINE: str = 'DEFAULT_NORMAL_BASELINE'
CONFIG_DEFAULT_GRAYS_BASELINE: str = 'DEFAULT_GRAYS_BASELINE'
CONFIG_DRIVER_SERIAL_PORT: str = 'DRIVER_SERIAL_PORT'

PRE_COMPILE_CMD: bool = config.get(CONFIG_PRE_COMPILE_CMD, True)
DRIVER_DEBUG_MODE: bool = config.get(CONFIG_DRIVER_DEBUG_MODE, False)
MOTOR_IDS: Tuple[int, int, int, int] = tuple(config.get(CONFIG_MOTOR_IDS, (4, 3, 1, 2)))
MOTOR_DIRS: Tuple[int, int, int, int] = tuple(config.get(CONFIG_MOTOR_DIRS, (-1, -1, 1, 1)))
HANG_TIME_MAX_ERROR: int = config.get(CONFIG_HANG_TIME_MAX_ERROR, 50)
TAG_GROUP: str = config.get(CONFIG_TAG_GROUP, 'tag36h11')
DEFAULT_EDGE_BASELINE: int = config.get(CONFIG_DEFAULT_EDGE_BASELINE, 1750)
DEFAULT_NORMAL_BASELINE: int = config.get(CONFIG_DEFAULT_NORMAL_BASELINE, 1000)
DEFAULT_GRAYS_BASELINE: int = config.get(CONFIG_DEFAULT_GRAYS_BASELINE, 1)
DRIVER_SERIAL_PORT: str = config.get(CONFIG_DRIVER_SERIAL_PORT, 'tty/USB0')

PATH_CACHE: str = os.path.join(PACKAGE_ROOT, DIR_CACHE)
PATH_LD: str = os.path.join(PACKAGE_ROOT, DIR_LID_SO)
HALT_CMD: bytes = b'v0\r'
BREAK_ACTION_KEY: str = 'break_action'
BREAKER_FUNC_KEY: str = 'breaker_func'
ACTION_DURATION: str = 'action_duration'
ACTION_SPEED_KEY: str = 'action_speed'
HANG_DURING_ACTION_KEY: str = 'hang_during_action'

FRONT_SENSOR_ID = (4,)
REAR_SENSOR_ID = (5,)
GRAYS_SENSOR_ID = (6, 7)
EDGE_FRONT_SENSOR_ID = (1, 2)
EDGE_REAR_SENSOR_ID = (0, 3)
SIDES_SENSOR_ID = (7, 8)

START_MAX_LINE: int = 1800
EDGE_MAX_LINE: int = 1750

FRONT_WATCHER_NAME: str = 'front_watcher'
REAR_WATCHER_NAME: str = 'rear_watcher'
EDGE_REAR_WATCHER_NAME: str = 'edge_rear_watcher'
EDGE_FRONT_WATCHER_NAME: str = 'edge_front_watcher'
SIDES_WATCHER_NAME: str = 'sides_watcher'
GRAYS_WATCHER_NAME: str = 'grays_watcher'
