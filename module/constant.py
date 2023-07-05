from typing import Tuple

FAN_GPIO_PWM: int = 18
FAN_pulse_frequency: int = 20000
FAN_duty_time_us: int = 1000000
FAN_PWN_range: int = 100

CACHE_DIR: str = 'cache'
LID_SO_DIR: str = 'lib'

ENV_LIB_SO_PATH: str = 'LIB_SO_PATH'
ENV_CACHE_DIR_PATH: str = 'CACHE_DIR_PATH'
ENV_PRE_COMPILE_CMD: str = 'PRE_COMPILE_CMD'

ZEROS: Tuple[int, int, int, int] = (0, 0, 0, 0)

CONFIG_PATH: str = './config.json'
