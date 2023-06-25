import os
import warnings
from typing import Callable
from .db_tools import persistent_lru_cache
from .constant import ENV_CACHE_DIR_PATH
from .algrithm_tools import list_multiply, multiply
from .timer import delay_ms
from .close_loop_controller import CloseLoopController

cache_dir = os.environ.get(ENV_CACHE_DIR_PATH)


class ActionFrame:
    controller = CloseLoopController(motor_ids_list=(4, 3, 1, 2)
                                     , debug=False)
    """
    [4]fl           fr[2]
           O-----O
              |
           O-----O
    [3]rl           rr[1]
    """

    def __init__(self, action_speed: int = 0, action_duration: int = 0,
                 action_speed_multiplier: float = 0,
                 action_duration_multiplier: float = 0,
                 action_speed_list: list[int, int, int, int] = (0, 0, 0, 0),
                 breaker_func: Callable[[], bool] = None,
                 break_action: object = None):
        """
        the minimal action unit that could be customized and glue together to be a chain movement,
        default stops the robot
        :param action_speed: the speed of the action
        :param action_duration: the duration of the action
        :param action_speed_multiplier: the speed multiplier
        :param action_duration_multiplier: the duration multiplier
        :param action_speed_list: the speed list of 4 wheels,positive value will drive the car forward,
                                    negative value is vice versa
        :param breaker_func: the action break judge,exit the action when the breaker returns True
        :param break_action: the object type is ActionFrame,
        the action that will be executed when the breaker is activated,
        """
        self._action_speed_list = None
        self._action_duration = None

        self._create_frame(action_speed=action_speed, action_speed_multiplier=action_speed_multiplier,
                           action_duration=action_duration, action_duration_multiplier=action_duration_multiplier,
                           action_speed_list=action_speed_list)

        self._breaker_func = breaker_func
        self._break_action = break_action

    def _create_frame(self,
                      action_speed: int, action_speed_multiplier,
                      action_duration: int, action_duration_multiplier: float,
                      action_speed_list):
        """
        load the params to attributes
        :param action_duration:
        :param action_duration_multiplier:
        :param action_speed:
        :param action_speed_list:
        :param action_speed_multiplier:
        :return:
        """
        if action_speed_list:
            # speed list will override the action_speed
            if action_speed_multiplier:
                # apply the multiplier
                action_speed_list = list_multiply(action_speed_list, action_speed_multiplier)
            self._action_speed_list = action_speed_list
        elif action_speed:
            if action_speed_multiplier:
                # apply the multiplier
                action_speed = multiply(action_speed, action_speed_multiplier)
            self._action_speed_list = [action_speed] * 4
        else:
            warnings.warn('##one of action_speed and action_speed_list must be specified##')
            self._action_speed_list = [0] * 4

        if action_duration_multiplier:
            # apply the multiplier
            # TODO: may actualize this multiplier Properties with a new class
            action_duration = multiply(action_duration, action_duration_multiplier)
        self._action_duration = action_duration

    def action_start(self) -> object or None:
        """
        execute the ActionFrame
        :return: None
        """
        # TODO: untested direction control
        self.controller.set_motors_speed(speed_list=self._action_speed_list,
                                         direction_list=[1, 1, -1, -1])
        if delay_ms(milliseconds=self._action_duration,
                    breaker_func=self._breaker_func):
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
    :keyword action_speed_list: list[int, int, int, int] = (0, 0, 0, 0)
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
        self._action_frame_stack: list[ActionFrame] = []

    def append(self, action: ActionFrame):
        """
        append new ActionFrame to the ActionFrame stack
        :param action: the ActionFrame to append
        :return: None
        """
        self._action_frame_stack.append(action)

    def extend(self, action_list: list[ActionFrame]):
        """
        extend ActionFrames stack with given ActionFrames
        :param action_list: the ActionFrames to extend
        :return: None
        """
        self._action_frame_stack += action_list

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
            break_action: ActionFrame or None = self._action_frame_stack.pop(0).action_start()
            if break_action:
                # the break action will override those ActionFrames that haven't been executed yet
                self._action_frame_stack.clear()
                self._action_frame_stack.append(break_action)
