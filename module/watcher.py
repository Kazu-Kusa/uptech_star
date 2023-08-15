from copy import copy
from typing import Callable, Sequence, Any, Tuple, Optional, Dict, List

from .onboardsensors import OnBoardSensors
from ..constant import EDGE_REAR_SENSOR_ID, EDGE_FRONT_SENSOR_ID, SIDES_SENSOR_ID, DEFAULT_EDGE_BASELINE, \
    START_MIN_LINE, \
    EDGE_REAR_WATCHER_NAME, EDGE_FRONT_WATCHER_NAME, SIDES_WATCHER_NAME, GRAYS_WATCHER_NAME, DEFAULT_GRAYS_BASELINE, \
    GRAYS_SENSOR_ID, FRONT_SENSOR_ID, REAR_SENSOR_ID, DEFAULT_NORMAL_BASELINE, FRONT_WATCHER_NAME, REAR_WATCHER_NAME

Watcher = Callable[[], bool]


# TODO: to manage all sort of breakers ,shall we create a registry system?
def build_watcher_simple(sensor_update: Callable[..., Sequence[Any]],
                         sensor_id: Tuple[int, ...],
                         min_line: Optional[int] = None,
                         max_line: Optional[int] = None,
                         args: Tuple = (),
                         kwargs: Dict[str, Any] = {}) -> Watcher:
    """
    构建传感器监视器函数。

    Args:
        sensor_update: 一个可调用对象，接受一个可选参数并返回一个序列。
        sensor_id: 传感器的ID，为整数的元组。
        min_line: 最小阈值，为整数。
        max_line: 最大阈值，为整数，默认为None。
        args: 可选参数的元组，默认为空元组。
        kwargs: 可选关键字参数的字典，默认为空字典。

    Returns:
        返回一个没有参数且返回布尔值的可调用对象，用于监视传感器数据是否在阈值范围内。
    Raises:
        无异常抛出。

    Example:
        # 创建 SensorData 实例
        sensor_data = SensorData()

        # 将类的 @property 属性作为 sensor_update 参数传入构造器
        test_watcher = build_watcher(sensor_data.sensor_update, (0, 1, 2), 5, 25)

        # 调用生成的监视器函数
        result = test_watcher()

        print(result)  # 输出：True
    """
    if max_line and min_line:
        def watcher() -> bool:
            return all((max_line > sensor_update(*args, **kwargs)[x] > min_line) for x in sensor_id)
    elif min_line:
        def watcher() -> bool:
            return all((sensor_update(*args, **kwargs)[x] > min_line) for x in sensor_id)
    else:
        def watcher() -> bool:
            return all((sensor_update(*args, **kwargs)[x] < max_line) for x in sensor_id)

    return watcher


def build_watcher_full_ctrl(sensor_update: Callable[..., Sequence[Any]],
                            sensor_id: Tuple[int, ...],
                            min_line: Sequence[Optional[int]] = None,
                            max_line: Sequence[Optional[int]] = None,
                            args: Tuple = (),
                            kwargs: Dict[str, Any] = {}) -> Watcher:
    """
    构建传感器监视器函数。

    Args:
        sensor_update: 一个可调用对象，接受一个可选参数并返回一个序列。
        sensor_id: 传感器的ID，为整数的元组。
        min_line: 最小阈值
        max_line: 最大阈值
        args: 可选参数的元组，默认为空元组。
        kwargs: 可选关键字参数的字典，默认为空字典。

    Returns:
        返回一个没有参数且返回布尔值的可调用对象，用于监视传感器数据是否在阈值范围内。

    Raises:
        无异常抛出。

    Example:
        # 创建 SensorData 实例
        sensor_data = SensorData()

        # 将类的 @property 属性作为 sensor_update 参数传入构造器
        test_watcher = build_watcher(sensor_data.sensor_update, (0, 1, 2), 5, 25)

        # 调用生成的监视器函数
        result = test_watcher()

        print(result)  # 输出：True
    """
    high_pass_sensors = []
    low_pass_sensors = []
    belt_pass_sensors = []

    for sensor_id, max_l, min_l in zip(sensor_id, max_line, min_line):
        if max_l and min_l :
            belt_pass_sensors.append((sensor_id, min_l, max_l))
        elif min_l:
            high_pass_sensors.append((sensor_id, min_l))
        elif max_l:
            low_pass_sensors.append((sensor_id, max_l))

    parts = []

    if belt_pass_sensors:
        parts.append(lambda update: all(x[1] < update[x[0]] < x[2] for x in belt_pass_sensors))

    if high_pass_sensors:
        parts.append(lambda update: all(x[1] < update[x[0]] for x in high_pass_sensors))

    if low_pass_sensors:
        parts.append(lambda update: all(x[1] > update[x[0]] for x in low_pass_sensors))

    def watcher() -> bool:
        update = sensor_update(*args, **kwargs)
        return all(part(update) for part in parts)

    return watcher


__BUFFER_list: List[List] = []


def build_delta_watcher(sensor_update: Callable[..., Sequence[Any]],
                        sensor_id: Tuple[int, ...],
                        max_line: Optional[int] = None,
                        min_line: Optional[int] = None,
                        args: Tuple = (),
                        kwargs: Dict[str, Any] = {}) -> Callable[[], bool]:
    __BUFFER_list.append([])
    buffer = copy(__BUFFER_list[-1])
    buffer[:] = sensor_update(*args, **kwargs)
    if max_line and min_line:
        def watcher() -> bool:
            nonlocal buffer
            update = sensor_update(*args, **kwargs)
            b = all((max_line > update[x] - buffer[x] > min_line) for x in sensor_id)
            buffer = update
            return b
    elif min_line:
        def watcher() -> bool:
            nonlocal buffer
            update = sensor_update(*args, **kwargs)
            b = all((update[x] - buffer[x] > min_line) for x in sensor_id)
            buffer = update
            return b
    else:
        def watcher() -> bool:
            nonlocal buffer
            update = sensor_update(*args, **kwargs)
            b = all((update[x] - buffer[x] < max_line) for x in sensor_id)
            buffer = update
            return b
    return watcher


default_edge_rear_watcher: Watcher = build_watcher_simple(sensor_update=OnBoardSensors.adc_all_channels,
                                                          sensor_id=EDGE_REAR_SENSOR_ID,
                                                          max_line=DEFAULT_EDGE_BASELINE)
default_rear_watcher: Watcher = build_watcher_simple(sensor_update=OnBoardSensors.adc_all_channels,
                                                     sensor_id=REAR_SENSOR_ID,
                                                     min_line=DEFAULT_NORMAL_BASELINE)

default_edge_front_watcher: Watcher = build_watcher_simple(sensor_update=OnBoardSensors.adc_all_channels,
                                                           sensor_id=EDGE_FRONT_SENSOR_ID,
                                                           max_line=DEFAULT_EDGE_BASELINE)

default_front_watcher: Watcher = build_watcher_simple(sensor_update=OnBoardSensors.adc_all_channels,
                                                      sensor_id=FRONT_SENSOR_ID,
                                                      min_line=DEFAULT_NORMAL_BASELINE)

default_sides_watcher: Watcher = build_watcher_simple(sensor_update=OnBoardSensors.adc_all_channels,
                                                      sensor_id=SIDES_SENSOR_ID,
                                                      max_line=START_MIN_LINE)

default_grays_watcher: Watcher = build_watcher_simple(sensor_update=OnBoardSensors.io_all_channels,
                                                      sensor_id=GRAYS_SENSOR_ID,
                                                      max_line=DEFAULT_GRAYS_BASELINE)
watchers = {EDGE_REAR_WATCHER_NAME: default_edge_rear_watcher,
            REAR_WATCHER_NAME: default_rear_watcher,
            EDGE_FRONT_WATCHER_NAME: default_edge_front_watcher,
            FRONT_WATCHER_NAME: default_front_watcher,
            SIDES_WATCHER_NAME: default_sides_watcher,
            GRAYS_WATCHER_NAME: default_grays_watcher}