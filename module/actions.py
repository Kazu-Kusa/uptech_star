import json
import time
import warnings
from functools import singledispatch
from typing import Tuple, Union, Optional, List, Dict, ByteString, Sequence

from dill import load, dump

from .algrithm_tools import multiply, factor_list_multiply
from .close_loop_controller import CloseLoopController
from .os_tools import persistent_cache
from .timer import delay_ms, calc_hang_time
from .watcher import watchers, Watcher
from ..constant import CACHE_DIR_PATH, ZEROS, PRE_COMPILE_CMD, MOTOR_IDS, HALT_CMD, MOTOR_DIRS, DRIVER_DEBUG_MODE, \
    BREAK_ACTION_KEY, BREAKER_FUNC_KEY, ACTION_DURATION, ACTION_SPEED_KEY, HANG_DURING_ACTION_KEY, DRIVER_SERIAL_PORT
from ..constant import HANG_TIME_MAX_ERROR

BreakActions = Tuple['ActionFrame', ...]


class ActionFrame(object):
    _controller: CloseLoopController = CloseLoopController(motor_ids=MOTOR_IDS, motor_dirs=MOTOR_DIRS,
                                                           debug=DRIVER_DEBUG_MODE, port=DRIVER_SERIAL_PORT)
    _instance_cache: Dict[Tuple, 'ActionFrame'] = {}
    _PRE_COMPILE_CMD: bool = PRE_COMPILE_CMD
    # TODO: since the PRE_COMPILE_CMD is not stored inside of the instance so we should clean the cache on it changed
    CACHE_FILE_NAME: str = 'ActionFrame_cache'
    _CACHE_FILE_PATH = f"{CACHE_DIR_PATH}\\{CACHE_FILE_NAME}"
    __is_break_action_verified_flag: str = 'is_break_action'
    print(f'Action Frame caches at [{_CACHE_FILE_PATH}]')

    @classmethod
    def close_port(cls):
        cls._controller.stop_msg_sending()

    @classmethod
    def open_port(cls):
        cls._controller.start_msg_sending()

    @classmethod
    def load_cache(cls) -> None:
        """
        load the action frame cache to class variable, using dill
        :return: None
        """
        try:
            with open(cls._CACHE_FILE_PATH, "rb") as file:
                cls._instance_cache = load(file)
        except FileNotFoundError:
            pass

    @classmethod
    def save_cache(cls, filter_breaker: bool = True) -> None:
        """
        Save the action frame cache to class variable, using dill
        Args:
            filter_breaker: whether to filter out the breaker action

        Returns:
            None

        """

        temp: Dict[Tuple, 'ActionFrame'] = {}
        if filter_breaker:
            warnings.warn('\nFiltering the breaker action out of cache before saving it\n'
                          'all deletions will be done on the DEEPCOPY of instance table')
            for item in cls._instance_cache.items():
                # remove  frames with breaker flag
                if not hasattr(item[1], cls.__is_break_action_verified_flag):
                    temp[item[0]] = item[1]
            warnings.warn(
                f'\nFiltered out {len(cls._instance_cache.keys()) - len(temp.keys())} action frames from cache\n\n')
        save_data = (temp if filter_breaker else cls._instance_cache)
        warnings.warn(f'\n##Saving Action Frame instance cache: \n'
                      f'\tCache Size: {len(save_data.keys())}')
        with open(cls._CACHE_FILE_PATH, "wb") as file:
            dump(save_data, file)

    def __new__(cls, *args, **kwargs):
        """
        will be called when a new instance is created
        functions varies depending on if the instance is cached:
        if the instance is cached: directly return the cached instance
        if the instance isn't cached: create a new instance and add it to the _instance_cache,and eventually return it

        :param args:args that will be passed to the new instance
        :param kwargs:kwargs that will be passed to the new instance
        """
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
                 breaker_func: Optional[Watcher] = None,
                 break_action: Optional[BreakActions] = None,
                 is_override_action: bool = True,
                 hang_time: float = 0.):
        """
        The minimal action unit that could be customized and glue together to be a chain movement,
        if no parameters are given,default parameters stop the robot
        :param action_speed: the speed of the action, accepts a tuple of 4 integers, each integer represents a motor
            speed,which can be either positive or negative.
            Index 0 is the front left motor.
            Index 1 is the back left motor.
            Index 2 is the back right motor.
            Index 3 is the front right motor.
            [0]fl         fr[3]
                  O-----O
                        |
                  O-----O
            [1]rl        rr[2]

        :param action_duration: the duration of the action accepts an integer only,and its unit is ms
        :param breaker_func: used to break the action during move,exit the action when the function returns True
        :param break_action: the action that will be executed when the breaker is activated,
            it should override all frames that haven't been executed, this logic is implemented in the ActionPlayer
        :param hang_time: the time during which the serial channel will be hanging up,to save the cpu time. Unit is s.
        """
        if break_action and not bool(breaker_func):
            # breaker_func can not be None as the break action is specified
            raise ValueError("breaker_func can not be None as the break action is specified")
        if self._PRE_COMPILE_CMD:
            if any(action_speed):
                # pre-compile the cmd into byte string that fits the driver's communication protocol
                self._action_cmd: ByteString = self._controller.makeCmds_dirs(action_speed)
                # pre-compile the cmd to save the time in string encoding in the future
            else:
                # stop cmd can be represented by a short broadcast cmd
                self._action_cmd: ByteString = HALT_CMD
        else:
            # if the pre-compile cmd is not used, just save the action speed
            self._action_speed_sequence: Tuple[int, int, int, int] = action_speed

        # convey the rest of the parameters
        self._action_duration: int = action_duration
        self._breaker_func: Watcher = breaker_func
        self._break_action: BreakActions = break_action
        self._is_override_action: bool = is_override_action
        self._hang_time: float = hang_time

        if breaker_func:
            # inject the flag to verify if this action is an action with break
            # which will be used in the caching section, because the breaker_func usually can't be cached
            setattr(self, self.__is_break_action_verified_flag, None)

    def action_start(self) -> Tuple[Optional[BreakActions], bool]:
        """
        execute the ActionFrame
        :return: the breaker action(s),the detailed implementation is at the ActionPlayer
        """
        if self._PRE_COMPILE_CMD:
            # if the pre-compile cmd is used, directly write the cmd to the serial queue
            self._controller.append_to_queue(byte_string=self._action_cmd, hang_time=self._hang_time)
        else:
            # if the pre-compile cmd is not used, just use the sealed method to implement the action
            self._controller.set_motors_speed(speed_list=self._action_speed_sequence, hang_time=self._hang_time)
        if delay_ms(milliseconds=self._action_duration, breaker_func=self._breaker_func) and self._action_duration:
            # if the breaker is activated, will return the break action with None check, which will be executed in
            # the ActionPlayer
            return self._break_action, self._is_override_action


def load_chain_actions_from_json(file_path: str, logging: bool = True) -> Dict[str, List]:
    """
   从 JSON 文件中递归加载创建链式动作

   Args:
       file_path (str): JSON 文件路径
       logging (bool):是否打印细节
   Returns:
       List[ActionFrame]: 创建的链式动作列表
   """

    # TODO: to prevent spelling errors , we should create a spell checker
    # TODO: should add a more powerful syntax check to reach a higher level of complexity
    @singledispatch
    def load_action_frame(unit: Union[List, Dict]) -> Optional[Union[ActionFrame, Tuple[ActionFrame, ...]]]:
        """
        递归加载动作帧数据
        Args:
            unit (dict): 动作帧数据的字典表示

        Returns:
            ActionFrame: 加载后的动作帧对象
        Exception:
            在未知数据类型上抛出 NotImplementedError
        Note:
            这个函数使用了@singledispatch构造了一个泛型递归加载函数，用作加载动作帧的配置文件

      """
        if unit is None:
            return None
        raise NotImplementedError('Unsupported data type')

    @load_action_frame.register(dict)
    def _(unit: Dict) -> ActionFrame:
        """
          从字典中加载 ActionFrame 对象。

        Args：
            data (Dict)：包含 ActionFrame 数据的字典。

        Returns：
            ActionFrame：加载的 ActionFrame 对象。

        Note：
            此函数被注册在 `load_action_frame` 装饰器下，用于将字典表示的 ActionFrame 反序列化为实际的 ActionFrame 对象。

        """
        if logging:
            print(f'Loading ActionFrame: \n'
                  f'\t{unit}')
        temp = unit.get(ACTION_SPEED_KEY, ZEROS)
        action_speed: Union[Tuple, int] = tuple(temp) if isinstance(temp, list) else temp
        action_duration: int = unit.get(ACTION_DURATION, 0)
        breaker_func: Watcher = watchers.get(unit.get(BREAKER_FUNC_KEY, None), None)
        break_action_data: List[Dict] = unit.get(BREAK_ACTION_KEY, None)
        hang_during_action: Optional[bool] = unit.get(HANG_DURING_ACTION_KEY, None)

        # 递归加载
        break_action = load_action_frame(break_action_data) if break_action_data else None

        return new_ActionFrame(
            action_speed=action_speed,
            action_duration=action_duration,
            breaker_func=breaker_func,
            break_action=break_action,
            hang_during_action=hang_during_action
        )

    @load_action_frame.register(list)
    def _(unit: List[Dict]) -> Tuple[ActionFrame, ...]:
        """
        Loads a list of ActionFrame objects from a list.
        Args:
            unit (List): The list containing the action frame data.

        Returns:
            List[ActionFrame]: The loaded list of ActionFrame objects.

        Note:
            This function is registered under the `load_action_frame` decorator and is used to deserialize
            a list representation of ActionFrames into a tuple of ActionFrame objects.
        """
        if logging:
            print(f'Loading ActionFrame Chain: \n'
                  f'\t{unit}')
        return tuple(load_action_frame(item) for item in unit)

    with open(file_path, 'r') as file:
        data: Dict[str, List] = json.load(file)  # load the Action config file into a dict
        for action_name in data.keys():
            # build List of ActionFrames to replace with the origin value in the loaded dict
            data[action_name] = [load_action_frame(action_data) for action_data in data.get(action_name, [])]

    return data


@persistent_cache(f'{CACHE_DIR_PATH}/new_action_frame_cache')
def new_ActionFrame(action_speed: Union[int, Tuple[int, int], Tuple[int, int, int, int]] = 0,
                    action_speed_multiplier: float = 0,
                    action_duration: int = 0,
                    action_duration_multiplier: float = 0,
                    breaker_func: Optional[Watcher] = None,
                    break_action: Optional[BreakActions] = None,
                    is_override_action: bool = True,
                    hang_during_action: Optional[bool] = None) -> ActionFrame:
    """
    an ActionFrame factory that generates a new action frame, with caching

    :keyword action_speed: allows 3 input styles:
        1.int: a single integer representing the speed of the all motors are the same speed
        2.Tuple[int,int,int,int]: a tuple of 4 integers representing the speed of the corresponding motors
        3.Tuple[int,int]: a tuple of 2 integers representing the speed of left motors and right motors

    :keyword action_duration: the action duration, in ms
    :keyword action_speed_multiplier: multiplier that will be applied to the action speed
    :keyword action_duration_multiplier: multiplier that will be applied to the action duration
    :keyword breaker_func: the breaker function to break the action
    :keyword break_action: the break action(s) that will be executed when the breaker is activated

    :keyword hang_during_action: if True, the serial channel will be hanging up to save the cpu time.
    :return: the desired ActionFrame object
    """
    action_speed_list = ZEROS
    if isinstance(action_speed, Tuple):
        if len(action_speed) == 2:
            action_speed_list = (action_speed[0],) * 2 + (action_speed[1],) * 2
        elif len(action_speed) == 4:
            action_speed_list = action_speed
    elif isinstance(action_speed, int):
        action_speed_list = (action_speed,) * 4
    else:
        raise TypeError('##UNKNOWN INPUT##')

    if action_speed_multiplier:
        # apply the multiplier
        action_speed_list = factor_list_multiply(action_speed_multiplier, action_speed_list)

    if action_duration_multiplier:
        # apply the multiplier
        action_duration = multiply(action_duration, action_duration_multiplier)
    return ActionFrame(action_speed=action_speed_list, action_duration=action_duration,
                       breaker_func=breaker_func, break_action=break_action, is_override_action=is_override_action,
                       hang_time=calc_hang_time(action_duration,
                                                HANG_TIME_MAX_ERROR)  # will be 0 if breaker is specified
                       if hang_during_action or breaker_func is None else 0)


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
    from .os_tools import CacheFILE
    CacheFILE.save_all_cache()
    ActionFrame.save_cache()


class ActionPlayer(object):
    def __init__(self):
        """
        action player, stores and plays the ActionFrames with in a queue
        """
        self._action_frame_queue: List[ActionFrame] = []

    @property
    def action_frame_queue(self) -> List[ActionFrame]:
        return self._action_frame_queue

    def append(self, action: ActionFrame, play_now: bool = True) -> None:
        """
        append new ActionFrame to the ActionFrame stack
        :param play_now: play on the ActionFrame added
        :param action: the ActionFrame to append
        :return: None
        """
        self._action_frame_queue.append(action)
        if play_now:
            self.play()

    def extend(self, actions: Sequence[ActionFrame], play_now: bool = True):
        """
        extend ActionFrames stack with given ActionFrames
        :param play_now: play on the ActionFrames added
        :param actions: the ActionFrames to extend
        :return: None
        """
        self._action_frame_queue.extend(actions)
        if play_now:
            self.play()

    def add(self, actions: Union[ActionFrame, Sequence[ActionFrame]]) -> None:
        if isinstance(actions, Sequence):
            self._action_frame_queue.extend(actions)
        elif isinstance(actions, ActionFrame):
            self._action_frame_queue.append(actions)
        else:
            raise TypeError('##UNKNOWN INPUT##')

    def clear(self) -> None:
        """
        clean the ActionFrames stack
        :return: None
        """
        self._action_frame_queue.clear()

    def override(self, actions: Union[ActionFrame, Sequence[ActionFrame]]):
        """
        override the ActionFrames queue
        :param actions:
        :return:
        """
        self._action_frame_queue.clear()
        self.add(actions)

    def play(self) -> None:
        """
        Play and remove the ActionFrames in the stack util there is it
        :return: None
        """
        while self._action_frame_queue:
            # if action exit because breaker then it should return the break action or None and the override flag
            break_action_data: Optional[Tuple[Optional[BreakActions], bool]] = self._action_frame_queue.pop(
                0).action_start()

            if break_action_data:
                if break_action_data[1]:
                    # the break action will override those ActionFrames that haven't been executed yet
                    self.override(break_action_data[0]) if break_action_data[0] else None
                else:
                    # the break action will not override those ActionFrames that haven't been executed
                    # the break action will be added to the ActionFrames queue at the beginning of the queue
                    self.insert_sequence(break_action_data[0])

    def insert_sequence(self, actions: Sequence[ActionFrame]):
        """
        insert a sequence of ActionFrames to the ActionFrames queue at the
        beginning of the queue
        :param actions: Sequence of ActionFrames to insert
        :return:
        """
        for action_frame in actions[::-1]:
            # reverse the sequence of ActionFrames to insert them in the correct order
            self._action_frame_queue.insert(0, action_frame)
