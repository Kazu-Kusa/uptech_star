import json
import os
import pickle
import time
import warnings
from functools import singledispatch
from typing import Callable, Tuple, Union, Optional, List, Dict, ByteString
from .db_tools import persistent_lru_cache
from ..constant import ENV_CACHE_DIR_PATH, ZEROS, PRE_COMPILE_CMD, MOTOR_IDS, HALT_CMD, MOTOR_DIRS, DRIVER_DEBUG_MODE, \
    BREAK_ACTION_KEY, BREAKER_FUNC_KEY, ACTION_DURATION, ACTION_SPEED_KEY, HANG_DURING_ACTION_KEY, DRIVER_SERIAL_PORT
from ..constant import HANG_TIME_MAX_ERROR
from .algrithm_tools import multiply, factor_list_multiply
from .timer import delay_ms, calc_hang_time
from .close_loop_controller import CloseLoopController, is_list_all_zero
from .watcher import watchers, Watcher

CACHE_DIR = os.environ.get(ENV_CACHE_DIR_PATH)


class ActionFrame:
    _controller: CloseLoopController = CloseLoopController(motor_ids=MOTOR_IDS, motor_dirs=MOTOR_DIRS,
                                                           debug=DRIVER_DEBUG_MODE, port=DRIVER_SERIAL_PORT)
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
                 break_action: Optional[Tuple[object, ...]] = None,
                 hang_time: float = 0.):
        """
        the minimal action unit that could be customized and glue together to be a chain movement,
        default stops the robot
        :param action_speed: the speed of the action
        :param action_duration: the duration of the action
        :param breaker_func: used to break the action during move,exit the action when the breaker returns True
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
        self._break_action: Tuple[object, ...] = break_action

        self._hang_time: float = hang_time
        # TODO:actually ,hang_time may have some conflicts with breaker_func

    def action_start(self) -> Optional[Tuple[object, ...]]:
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
    @singledispatch
    def load_action_frame(data: Union[List, Dict]) -> Optional[Union[ActionFrame, Tuple[ActionFrame, ...]]]:
        """
          加载动作帧数据

          Args:
              data (dict): 动作帧数据的字典表示

          Returns:
              ActionFrame: 加载后的动作帧对象
          Note:
              这个函数使用了@singledispatch构造了一个泛型递归加载函数，用作加载动作帧的配置文件
      """
        if data is None:
            return None
        raise NotImplementedError('Unsupported data type')

    @load_action_frame.register(dict)
    def _(data: Dict) -> ActionFrame:
        """
          从字典中加载 ActionFrame 对象。

        参数：
            data (Dict)：包含 ActionFrame 数据的字典。

        返回值：
            ActionFrame：加载的 ActionFrame 对象。

        异常：
            TypeError：如果提供的数据不是字典类型或缺少必要的属性。

        注意：
            此函数被注册在 `load_action_frame` 装饰器下，用于将字典表示的 ActionFrame 反序列化为实际的 ActionFrame 对象。

        """
        if logging:
            print(f'Loading ActionFrame: \n'
                  f'\t{data}')
        temp = data.get(ACTION_SPEED_KEY, ZEROS)
        action_speed: Union[Tuple, int] = tuple(temp) if isinstance(temp, list) else temp
        action_duration: int = data.get(ACTION_DURATION, 0)
        breaker_func: Watcher = watchers.get(data.get(BREAKER_FUNC_KEY, None), None)
        break_action_data: List[Dict] = data.get(BREAK_ACTION_KEY, None)
        hang_during_action: Optional[bool] = data.get(HANG_DURING_ACTION_KEY, None)

        break_action = load_action_frame(break_action_data) if break_action_data else None

        return new_ActionFrame(
            action_speed=action_speed,
            action_duration=action_duration,
            breaker_func=breaker_func,
            break_action=break_action,
            hang_during_action=hang_during_action
        )

    @load_action_frame.register(list)
    def _(data: List[Dict]) -> Tuple[ActionFrame, ...]:
        """
        Loads a list of ActionFrame objects from a list.

        Args:
            data (List): The list containing the action frame data.

        Returns:
            List[ActionFrame]: The loaded list of ActionFrame objects.

        Raises:
            TypeError: If the provided data is not of type list or is missing required attributes.

        Note:
            This function is registered under the `load_action_frame` decorator and is used to deserialize
            a list representation of ActionFrames into a list of ActionFrame objects.
        """
        if logging:
            print(f'Loading ActionFrame Chain: \n'
                  f'\t{data}')
        return tuple(load_action_frame(item) for item in data)

    with open(file_path, 'r') as file:
        data: Dict[str, List] = json.load(file)  # load the Action config file into a dict
        for action_name in data.keys():
            # build List of ActionFrames to replace with the origin value in the loaded dict
            data[action_name] = [load_action_frame(action_data) for action_data in data.get(action_name, [])]

    return data


@persistent_lru_cache(f'{CACHE_DIR}/new_action_frame_cache')
def new_ActionFrame(action_speed: Union[int, Tuple[int, int], Tuple[int, int, int, int]] = 0,
                    action_speed_multiplier: float = 0,
                    action_duration: int = 0,
                    action_duration_multiplier: float = 0,
                    breaker_func: Optional[Callable[[], bool]] = None,
                    break_action: Optional[Union[ActionFrame, Tuple[ActionFrame]]] = None,
                    hang_during_action: Optional[bool] = None) -> ActionFrame:
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
    action_speed_list = ZEROS
    if isinstance(action_speed, Tuple):
        if len(action_speed) == 2:
            action_speed_list = (action_speed[0],) * 2 + (action_speed[1],) * 2
        elif len(action_speed) == 4:
            action_speed_list = action_speed
    elif isinstance(action_speed, int):
        action_speed_list = (action_speed,) * 4
    else:
        warnings.warn('##UNKNOWN INPUT##')

    if action_speed_multiplier:
        # apply the multiplier
        action_speed_list = factor_list_multiply(action_speed_multiplier, action_speed_list)

    if action_duration_multiplier:
        # apply the multiplier
        action_duration = multiply(action_duration, action_duration_multiplier)
    return ActionFrame(action_speed=action_speed_list, action_duration=action_duration,
                       breaker_func=breaker_func, break_action=break_action,
                       hang_time=calc_hang_time(action_duration, HANG_TIME_MAX_ERROR)
                       if hang_during_action or (hang_during_action is None and not bool(breaker_func)) else 0)


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
