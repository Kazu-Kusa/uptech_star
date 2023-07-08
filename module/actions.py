import os
import pickle
import time
import warnings
from typing import Callable, Tuple, Union, Optional, List, Dict, ByteString
from .db_tools import persistent_lru_cache
from ..constant import ENV_CACHE_DIR_PATH, ZEROS, PRE_COMPILE_CMD, MOTOR_IDS, HALT_CMD, MOTOR_DIRS, DRIVER_DEBUG_MODE
from ..constant import HANG_TIME_MAX_ERROR
from .algrithm_tools import multiply, factor_list_multiply
from .timer import delay_ms, calc_hang_time
from .close_loop_controller import CloseLoopController, is_list_all_zero

CACHE_DIR = os.environ.get(ENV_CACHE_DIR_PATH)


class ActionFrame:
    _controller: CloseLoopController = CloseLoopController(motor_ids=MOTOR_IDS, motor_dirs=MOTOR_DIRS,
                                                           debug=DRIVER_DEBUG_MODE)
    _instance_cache: Dict = {}
    _PRE_COMPILE_CMD: bool = PRE_COMPILE_CMD
    # TODO: since the PRE_COMPILE_CMD is not stored inside of the instance so we should clean the cache on it changed
    CACHE_FILE_NAME: str = 'ActionFrame_cache'
    _CACHE_FILE_PATH = f"{CACHE_DIR}\\{CACHE_FILE_NAME}"
    print(f'Action Frame caches at [{_CACHE_FILE_PATH}]')
    """
    [4]fl           fr[2]
           O-----O
              |
           O-----O
    [3]rl           rr[1]
    """

    @classmethod
    def load_cache(cls):
        try:
            with open(cls._CACHE_FILE_PATH, "rb") as file:
                cls._instance_cache = pickle.load(file)
        except FileNotFoundError:
            pass

    @classmethod
    def save_cache(cls):
        print(f'##Saving Action Frame instance cache: \n'
              f'\tCache Size: {len(cls._instance_cache.items())}')

        with open(cls._CACHE_FILE_PATH, "wb") as file:
            pickle.dump(cls._instance_cache, file)

    def __new__(cls, *args, **kwargs):
        # Check if the instance exists in the cache
        key = (args, tuple(kwargs.items()))
        if key in cls._instance_cache:
            return cls._instance_cache[key]

        # Create a new instance and add it to the cache
        instance = super().__new__(cls)
        cls._instance_cache[key] = instance
        return instance

    def __init__(self,
                 action_speed: Tuple[int, int, int, int] = ZEROS,
                 action_duration: int = 0,
                 breaker_func: Optional[Callable[[], bool]] = None,
                 break_action: Optional[object] = None,
                 hang_time: float = 0.):
        """
        the minimal action unit that could be customized and glue together to be a chain movement,
        default stops the robot
        :param action_speed: the speed of the action
        :param action_duration: the duration of the action
        :param breaker_func: the action break judge,exit the action when the breaker returns True
        :param break_action: the object type is ActionFrame,
        the action that will be executed when the breaker is activated,
        """

        if self._PRE_COMPILE_CMD:
            # pre-compile the command
            if is_list_all_zero(action_speed):
                # stop cmd can be represented by a short broadcast cmd
                self._action_cmd: ByteString = HALT_CMD
            else:

                self._action_cmd: ByteString = self._controller.makeCmds_dirs(action_speed)
        else:
            self._action_speed_list: Tuple[int, int, int, int] = action_speed
        self._action_duration: int = action_duration
        self._breaker_func: Callable[[], bool] = breaker_func
        self._break_action: object = break_action

        self._hang_time: float = hang_time
        # TODO:actually ,hang_time may have some conflicts with breaker_func

    def action_start(self) -> Optional[Union[object, List[object]]]:
        """
        execute the ActionFrame
        :return: None
        """
        # TODO: untested direction control
        # TODO: untested precompile option

        if self._PRE_COMPILE_CMD:
            self._controller.append_to_stack(byte_string=self._action_cmd, hang_time=self._hang_time)
        else:
            self._controller.set_motors_speed(speed_list=self._action_speed_list)
        if self._action_duration and delay_ms(milliseconds=self._action_duration, breaker_func=self._breaker_func):
            return self._break_action


@persistent_lru_cache(f'{CACHE_DIR}/new_action_frame_cache', maxsize=None)
def new_ActionFrame(action_speed: Union[int, Tuple[int, int], Tuple[int, int, int, int]] = 0,
                    action_speed_multiplier: float = 0,
                    action_duration: int = 0,
                    action_duration_multiplier: float = 0,
                    breaker_func: Optional[Callable[[], bool]] = None,
                    break_action: Optional[Union[object, List[object]]] = None,
                    hang_during_action: bool = False) -> ActionFrame:
    """
    generates a new action frame ,with LRU caching rules

    :keyword action_speed: int = 0
    :keyword action_duration: int = 0
    :keyword action_speed_multiplier: float = 0
    :keyword action_duration_multiplier: float = 0
    :keyword breaker_func: Callable[[], bool] = None
    :keyword break_action: object = None
    :return: the ActionFrame object
    """
    if isinstance(action_speed, Tuple) and len(action_speed) == 2:
        if action_speed_multiplier:
            # apply the multiplier
            action_speed = factor_list_multiply(action_speed_multiplier, action_speed)
        action_speed_list = (action_speed[0], action_speed[0], action_speed[1], action_speed[1])
    elif isinstance(action_speed, int):
        # speed list will override the action_speed
        if action_speed_multiplier:
            # apply the multiplier
            action_speed = multiply(action_speed, action_speed_multiplier)
        action_speed_list = tuple([action_speed] * 4)
    elif isinstance(action_speed, Tuple) and len(action_speed) == 4:
        if action_speed_multiplier:
            action_speed = factor_list_multiply(action_speed_multiplier, action_speed)
        action_speed_list = tuple(action_speed)
    else:
        warnings.warn('##UNKNOWN INPUT##')
        action_speed_list = ZEROS
    if action_duration_multiplier:
        # apply the multiplier
        # TODO: may actualize this multiplier Properties with a new class
        action_duration = multiply(action_duration, action_duration_multiplier)
    return ActionFrame(action_speed=action_speed_list, action_duration=action_duration,
                       breaker_func=breaker_func, break_action=break_action,
                       hang_time=calc_hang_time(action_duration, HANG_TIME_MAX_ERROR) if hang_during_action else 0)


def pre_build_action_frame(speed_range: Tuple[int, int, int], duration_range: Tuple[int, int, int]):
    print('building')
    ActionFrame.load_cache()
    start = time.time()
    for speed in range(*speed_range):
        for duration in range(*duration_range):
            # print(f'building speed: {speed}|duration: {duration}')
            new_ActionFrame(action_speed=speed,
                            action_duration=duration)

    print(f'time cost: {time.time() - start:.6f}s')
    from .db_tools import CacheFILE
    CacheFILE.save_all_cache()
    ActionFrame.save_cache()


class ActionPlayer:
    def __init__(self):
        """
        action player,stores and plays the ActionFrames with stack
        """
        self._action_frame_queue: List[ActionFrame] = []

    @property
    def action_frame_stack(self):
        return self._action_frame_queue

    def append(self, action: ActionFrame, play_now: bool = True):
        """
        append new ActionFrame to the ActionFrame stack
        :param play_now: play on the ActionFrame added
        :param action: the ActionFrame to append
        :return: None
        """
        self._action_frame_queue.append(action)
        if play_now:
            self.play()

    def extend(self, action_list: List[ActionFrame], play_now: bool = True):
        """
        extend ActionFrames stack with given ActionFrames
        :param play_now: play on the ActionFrames added
        :param action_list: the ActionFrames to extend
        :return: None
        """
        self._action_frame_queue.extend(action_list)
        if play_now:
            self.play()

    def add(self, actions: Union[ActionFrame, List[ActionFrame]]):
        if isinstance(actions, List):
            self._action_frame_queue.extend(actions)
        else:
            self._action_frame_queue.append(actions)

    def clear(self):
        """
        clean the ActionFrames stack
        :return: None
        """
        self._action_frame_queue.clear()

    def play(self):
        """
        Play and remove the ActionFrames in the stack util there is it
        :return: None
        """
        while self._action_frame_queue:
            # if action exit because breaker then it should return the break action or None
            break_action: Optional[Union[ActionFrame, List[ActionFrame]]] = self._action_frame_queue.pop(
                0).action_start()
            if break_action:
                # the break action will override those ActionFrames that haven't been executed yet
                self._action_frame_queue.clear()
                self.add(break_action)
