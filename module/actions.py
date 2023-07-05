import os
import pickle
import time
import warnings
from typing import Callable, Tuple, Union, Optional, List, Dict, ByteString
from .db_tools import persistent_lru_cache
from .constant import ENV_CACHE_DIR_PATH, ZEROS, PRE_COMPILE_CMD, MOTOR_ID_LIST
from .algrithm_tools import multiply, factor_list_multiply
from .timer import delay_ms
from .close_loop_controller import CloseLoopController

CACHE_DIR = os.environ.get(ENV_CACHE_DIR_PATH)


class ActionFrame:
    _controller: CloseLoopController = CloseLoopController(motor_ids_list=MOTOR_ID_LIST, debug=False)
    _instance_cache: Dict = {}
    PRE_COMPILE_CMD: bool = PRE_COMPILE_CMD
    CACHE_FILE_NAME: str = 'ActionFrame_cache'
    CACHE_FILE_PATH = f"{CACHE_DIR}\\{CACHE_FILE_NAME}"
    print(f'Action Frame caches at [{CACHE_FILE_PATH}]')
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
            with open(cls.CACHE_FILE_PATH, "rb") as file:
                cls._instance_cache = pickle.load(file)
        except FileNotFoundError:
            pass

    @classmethod
    def save_cache(cls):
        with open(cls.CACHE_FILE_PATH, "wb+") as file:
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
                 break_action: Optional[object] = None):
        """
        the minimal action unit that could be customized and glue together to be a chain movement,
        default stops the robot
        :param action_speed: the speed of the action
        :param action_duration: the duration of the action
        :param breaker_func: the action break judge,exit the action when the breaker returns True
        :param break_action: the object type is ActionFrame,
        the action that will be executed when the breaker is activated,
        """
        self._action_speed_list: Tuple[int, int, int, int] = action_speed
        if self.PRE_COMPILE_CMD:
            self._action_cmd: ByteString = self._controller.makeCmd_list(self._action_speed_list)
        self._action_duration: int = action_duration
        self._breaker_func: Callable[[], bool] = breaker_func
        self._break_action: object = break_action

    def action_start(self) -> Optional[Union[object, List[object]]]:
        """
        execute the ActionFrame
        :return: None
        """
        # TODO: untested direction control
        # TODO: untested precompile option
        if self.PRE_COMPILE_CMD:
            self._controller.write_to_serial(byte_string=self._action_cmd)
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
                    break_action: Optional[Union[object, List[object]]] = None) -> ActionFrame:
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
                       breaker_func=breaker_func, break_action=break_action)


def pre_build_action_frame(speed_range: Tuple[int, int, int], duration_range: Tuple[int, int, int]):
    print('building')
    start = time.time()
    for speed in range(*speed_range):
        for duration in range(*duration_range):
            # print(f'building speed: {speed}|duration: {duration}')
            new_ActionFrame(action_speed=speed,
                            action_duration=duration)
    print(f'time cost: {time.time() - start:.2f}s')


class ActionPlayer:
    def __init__(self):
        """
        action player,stores and plays the ActionFrames with stack
        """
        self._action_frame_stack: List[ActionFrame] = []

    @property
    def action_frame_stack(self):
        return self._action_frame_stack

    def append(self, action: ActionFrame, play_now: bool = True):
        """
        append new ActionFrame to the ActionFrame stack
        :param play_now: play on the ActionFrame added
        :param action: the ActionFrame to append
        :return: None
        """
        self._action_frame_stack.append(action)
        if play_now:
            self.play()

    def extend(self, action_list: List[ActionFrame], play_now: bool = True):
        """
        extend ActionFrames stack with given ActionFrames
        :param play_now: play on the ActionFrames added
        :param action_list: the ActionFrames to extend
        :return: None
        """
        self._action_frame_stack.extend(action_list)
        if play_now:
            self.play()

    def add(self, actions: Union[ActionFrame, List[ActionFrame]]):
        if isinstance(actions, List):
            self._action_frame_stack.extend(actions)
        else:
            self._action_frame_stack.append(actions)

    def clear(self):
        """
        clean the ActionFrames stack
        :return: None
        """
        self._action_frame_stack.clear()

    def play(self):
        """
        Play and remove the ActionFrames in the stack util there is it
        :return: None
        """
        while self._action_frame_stack:
            # if action exit because breaker then it should return the break action or None
            break_action: Optional[Union[ActionFrame, List[ActionFrame]]] = self._action_frame_stack.pop(
                0).action_start()
            if break_action:
                # the break action will override those ActionFrames that haven't been executed yet
                self._action_frame_stack.clear()
                self.add(break_action)
