import os
import warnings
from typing import Callable, Tuple, Union, Optional, List
from .db_tools import persistent_lru_cache
from .constant import ENV_CACHE_DIR_PATH
from .algrithm_tools import multiply, factor_list_multiply
from .timer import delay_ms
from .close_loop_controller import CloseLoopController

cache_dir = os.environ.get(ENV_CACHE_DIR_PATH)


class ActionFrame:
    controller = CloseLoopController(motor_ids_list=(4, 3, 1, 2), debug=False)
    zeros = (0, 0, 0, 0)
    """
    [4]fl           fr[2]
           O-----O
              |
           O-----O
    [3]rl           rr[1]
    """

    def __init__(self, action_speed: Union[int, Tuple[int, int], Tuple[int, int, int, int]] = 0,
                 action_speed_multiplier: float = 0,
                 action_duration: int = 0,
                 action_duration_multiplier: float = 0,
                 breaker_func: Optional[Callable[[], bool]] = None,
                 break_action: Optional[object] = None):
        """
        the minimal action unit that could be customized and glue together to be a chain movement,
        default stops the robot
        :param action_speed: the speed of the action
        :param action_duration: the duration of the action
        :param action_speed_multiplier: the speed multiplier
        :param action_duration_multiplier: the duration multiplier
        :param breaker_func: the action break judge,exit the action when the breaker returns True
        :param break_action: the object type is ActionFrame,
        the action that will be executed when the breaker is activated,
        """
        self._action_speed_list: Union[Tuple[int, int, int, int], List[int]] = []
        self._action_duration: int = 0
        self._breaker_func: Callable[[], bool] = breaker_func
        self._break_action: object = break_action
        self._create_frame(action_speed=action_speed, action_speed_multiplier=action_speed_multiplier,
                           action_duration=action_duration, action_duration_multiplier=action_duration_multiplier)

    def _create_frame(self,
                      action_speed: Union[int, Tuple[int, int], Tuple[int, int, int, int]],
                      action_speed_multiplier: float,
                      action_duration: int,
                      action_duration_multiplier: float):
        """
        load the params to attributes
        :param action_duration:
        :param action_duration_multiplier:
        :param action_speed:
        :param action_speed_multiplier:
        :return:
        """
        if isinstance(action_speed, Tuple) and len(action_speed) == 2:
            if action_speed_multiplier:
                # apply the multiplier
                action_speed = factor_list_multiply(action_speed_multiplier, action_speed)
            self._action_speed_list = (action_speed[0], action_speed[0], action_speed[1], action_speed[1])
        elif isinstance(action_speed, int):
            # speed list will override the action_speed
            if action_speed_multiplier:
                # apply the multiplier
                action_speed = multiply(action_speed, action_speed_multiplier)
            self._action_speed_list = tuple([action_speed] * 4)
        elif isinstance(action_speed, Tuple) and len(action_speed) == 4:
            if action_speed_multiplier:
                action_speed = factor_list_multiply(action_speed_multiplier, action_speed)
            self._action_speed_list = tuple(action_speed)
        else:
            warnings.warn('##UNKNOWN INPUT##')
            self._action_speed_list = self.zeros
        if action_duration_multiplier:
            # apply the multiplier
            # TODO: may actualize this multiplier Properties with a new class
            action_duration = multiply(action_duration, action_duration_multiplier)

        self._action_duration = action_duration

    def action_start(self) -> Optional[object]:
        """
        execute the ActionFrame
        :return: None
        """
        # TODO: untested direction control

        self.controller.set_motors_speed(speed_list=self._action_speed_list)
        if self._action_duration and delay_ms(milliseconds=self._action_duration, breaker_func=self._breaker_func):
            return self._break_action


@persistent_lru_cache(CACHE_FILE=f'{cache_dir}/new_action_frame_cache', maxsize=1024)
def new_ActionFrame(**kwargs) -> ActionFrame:
    """
    generates a new action frame ,with LRU caching rules
    :param kwargs: the arguments that will be passed to the ActionFrame constructor

    :keyword action_speed: int = 0
    :keyword action_duration: int = 0
    :keyword action_speed_multiplier: float = 0
    :keyword action_duration_multiplier: float = 0
    :keyword breaker_func: Callable[[], bool] = None
    :keyword break_action: object = None
    :return: the ActionFrame object
    """
    return ActionFrame(**kwargs)


class ActionPlayer:
    def __init__(self):
        """
        action player,stores and plays the ActionFrames with stack
        """
        self._action_frame_stack: List[ActionFrame] = []

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
            break_action: Optional[ActionFrame] = self._action_frame_stack.pop(0).action_start()
            if break_action:
                # the break action will override those ActionFrames that haven't been executed yet
                self._action_frame_stack.clear()
                self._action_frame_stack.append(break_action)
