from functools import lru_cache
from typing import Callable, final

from .algrithm_tools import list_multiply, multiply
from .timer import delay_ms
from .up_controller import UpController


class ActionFrame:
    controller = UpController(debug=False, fan_control=False)
    zeros = (0, 0, 0, 0)
    """
    fl           fr
        O-----O
           |
        O-----O
    rl           rr
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
        :param action_speed_list: the speed list of 4 wheels
        :param breaker_func: the action break judge,exit the action when the breaker returns True
        :param break_action: the object type is ActionFrame,the action that will be executed when the breaker is activated,
        """
        self._action_speed_list = None
        self._action_speed = None
        self._action_duration = None

        self._create_frame(action_duration, action_duration_multiplier, action_speed, action_speed_list,
                           action_speed_multiplier)

        self._breaker_func = breaker_func
        self._break_action = break_action

    @final
    def _create_frame(self, action_duration, action_duration_multiplier, action_speed, action_speed_list,
                      action_speed_multiplier):
        if self._action_speed_list:
            # speed list will override the action_speed
            if action_speed_multiplier:
                action_speed_list = list_multiply(action_speed_list, action_speed_multiplier)
            self._action_speed_list = action_speed_list
        else:
            if action_speed_multiplier:
                action_speed = multiply(action_speed, action_speed_multiplier)
            self._action_speed = action_speed

        if action_duration_multiplier:
            action_duration = multiply(action_duration, action_duration_multiplier)
        self._action_duration = action_duration

    def action_start(self) -> object or None:
        def action() -> ActionFrame or None:
            self.controller.set_all_motors_speed(self._action_speed)
            if delay_ms(milliseconds=self._action_duration,
                        breaker_func=self._breaker_func):
                return self._break_action

        def action_with_speed_list() -> ActionFrame or None:
            self.controller.set_motors_speed(self._action_speed_list)
            if delay_ms(milliseconds=self._action_duration,
                        breaker_func=self._breaker_func):
                return self._break_action

        if self._action_speed_list:
            return action_with_speed_list()
        else:
            return action()


@lru_cache(maxsize=512)
def new_action_frame(**kwargs) -> ActionFrame:
    """
    generates a new action frame ,with LRU caching rules
    :param kwargs: the arguments that will be passed to the ActionFrame constructor
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
            next_action: ActionFrame or None = self._action_frame_stack.pop(0).action_start()
            if next_action:
                self._action_frame_stack.append(next_action)
