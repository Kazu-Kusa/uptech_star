from copy import deepcopy
from typing import Callable, Sequence, Any, Tuple, Optional, Dict, List

from .onboardsensors import OnBoardSensors
from ..constant import EDGE_REAR_SENSOR_ID, EDGE_FRONT_SENSOR_ID, SIDES_SENSOR_ID, DEFAULT_EDGE_BASELINE, \
    START_MIN_LINE, \
    EDGE_REAR_WATCHER_NAME, EDGE_FRONT_WATCHER_NAME, SIDES_WATCHER_NAME, GRAYS_WATCHER_NAME, DEFAULT_GRAYS_BASELINE, \
    GRAYS_SENSOR_ID, FRONT_SENSOR_ID, REAR_SENSOR_ID, DEFAULT_NORMAL_BASELINE, FRONT_WATCHER_NAME, REAR_WATCHER_NAME

Watcher = Callable[[], bool]


def watchers_merge(watcher_sequence: Sequence[Watcher], use_any: bool = False) -> Watcher:
    """
    merge all the watchers in the sequence
    Args:
        use_any:
        watcher_sequence:

    Returns:

    """
    logic_calc_func = any if use_any else all

    def merged_watcher() -> bool:
        return logic_calc_func(watcher() for watcher in watcher_sequence)

    return merged_watcher


def build_io_watcher_from_indexed(sensor_update: Callable[[int], int],
                                  sensor_ids: Sequence[int],
                                  activate_status_describer: Sequence[int],
                                  use_any: bool = False) -> Watcher:
    """
    use indexed io updater to construct watcher
    Args:
        sensor_update ():
        sensor_ids ():
        activate_status_describer ():
        use_any ():

    Returns:

    """
    if len(sensor_ids) != len(activate_status_describer):
        raise IndexError('should be with same length')
    logic_calc_func = any if use_any else all

    def _watcher() -> bool:
        return logic_calc_func(
            sensor_update(sensor_id) == describer for sensor_id, describer in
            zip(sensor_ids, activate_status_describer))

    return _watcher


# TODO: to manage all sort of breakers ,shall we create a registry system?
def build_watcher_simple(sensor_update: Callable[..., Sequence[Any]],
                         sensor_id: Tuple[int, ...],
                         min_line: Optional[int] = None,
                         max_line: Optional[int] = None,
                         use_any: bool = False,
                         args: Tuple = (),
                         kwargs: Dict[str, Any] = {}) -> Watcher:
    """
    构建传感器监视器函数。

    Args:
        sensor_update: 一个可调用对象，接受一个可选参数并返回一个序列。
        sensor_id: 传感器的ID，为整数的元组。
        min_line: 最小阈值，为整数。
        max_line: 最大阈值，为整数，默认为None。
        use_any: 逻辑判断类型，True为取或，False为取并
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
    logic_calc_func = any if use_any else all
    if max_line and min_line:
        def watcher() -> bool:
            update = sensor_update(*args, **kwargs)
            return logic_calc_func((max_line > update[x] > min_line) for x in sensor_id)
    elif min_line:
        def watcher() -> bool:
            update = sensor_update(*args, **kwargs)
            return logic_calc_func((update[x] > min_line) for x in sensor_id)
    else:
        def watcher() -> bool:
            update = sensor_update(*args, **kwargs)
            return logic_calc_func((update[x] < max_line) for x in sensor_id)

    return watcher


def build_watcher_full_ctrl(sensor_update: Callable[..., Sequence[Any]],
                            sensor_ids: Sequence[int],
                            min_lines: Sequence[Optional[int]] = None,
                            max_lines: Sequence[Optional[int]] = None,
                            use_any: bool = False,
                            args: Tuple = (),
                            kwargs: Dict[str, Any] = {}) -> Watcher:
    """
    构建传感器监视器函数。

    Args:
        sensor_update: 一个可调用对象，接受一个可选参数并返回一个序列。
        sensor_ids: 传感器的ID，为整数的元组。
        min_lines: 最小阈值
        max_lines: 最大阈值
        use_any: 逻辑判断类型，True为取或，False为取并
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

    logic_calc_func = any if use_any else all
    belt_pass_sensors, high_pass_sensors, low_pass_sensors = sort_with_mode(max_lines, min_lines, sensor_ids)

    # build the watcher components
    parts = []

    if belt_pass_sensors:
        parts.append(lambda update: logic_calc_func(x[1] < update[x[0]] < x[2] for x in belt_pass_sensors))

    if high_pass_sensors:
        parts.append(lambda update: logic_calc_func(x[1] < update[x[0]] for x in high_pass_sensors))

    if low_pass_sensors:
        parts.append(lambda update: logic_calc_func(x[1] > update[x[0]] for x in low_pass_sensors))

    def watcher() -> bool:
        f"""
        Assemble the watcher with all the parts.
        Returns: True if all the parts return True

        Notes:
            parts parameters are as follows
        
            sensor_id: {sensor_ids}
            min_line: {min_lines}
            max_line: {max_lines}
        
        """
        update = sensor_update(*args, **kwargs)
        return logic_calc_func(part(update) for part in parts)

    return watcher


def sort_with_mode(max_lines, min_lines, sensor_ids) -> Tuple[
    List[Tuple[int, int, int]], List[Tuple[int, int]], List[Tuple[int, int]]]:
    """
    from the input infer the judge mode of the sensors
    Args:
        max_lines:
        min_lines:
        sensor_ids:

    Returns:

    """
    if not len(min_lines) == len(max_lines) == len(sensor_ids):
        raise ValueError("min_line and max_line should have the same length as sensor_id does")
    # sort the sensors according to their mode, which defined by min_line and max_line
    high_pass_sensors = []
    low_pass_sensors = []
    belt_pass_sensors = []
    for sensor_ids, max_l, min_l in zip(sensor_ids, max_lines, min_lines):
        if max_l and min_l:
            belt_pass_sensors.append((sensor_ids, min_l, max_l))
        elif min_l:
            high_pass_sensors.append((sensor_ids, min_l))
        elif max_l:
            low_pass_sensors.append((sensor_ids, max_l))
    return belt_pass_sensors, high_pass_sensors, low_pass_sensors


class BufferRegistry(object):
    """
    a Buffer class to store the previous sensor updates
    """
    __BUFFER_Dict: Dict[int, Any] = {}
    __client_count = 0

    @classmethod
    def register_buffer(cls) -> int:
        cls.__client_count += 1
        cls.__BUFFER_Dict[cls.__client_count] = None
        return cls.__client_count

    @classmethod
    def set_buffer(cls, key: int, value: Any):
        cls.__BUFFER_Dict[key] = deepcopy(value)

    @classmethod
    def get_buffer(cls, key: int) -> Any:
        return cls.__BUFFER_Dict.get(key)

    @classmethod
    def buffer_dict(cls) -> Dict[int, Any]:
        return cls.__BUFFER_Dict


def build_delta_watcher_simple(sensor_update: Callable[..., Sequence[Any]],
                               sensor_id: Tuple[int, ...],
                               max_line: Optional[int] = None,
                               min_line: Optional[int] = None,
                               use_any: bool = False,
                               args: Tuple = (),
                               kwargs: Dict[str, Any] = {}) -> Watcher:
    """
    Build a delta watcher function that checks for changes in sensor readings.

    Args:
    - sensor_update: A function that retrieves the latest sensor readings.
    - sensor_id: A tuple of indices representing the sensor values to monitor for changes.
    - max_line: The maximum difference allowed between the current and previous sensor readings.
    - min_line: The minimum difference required between the current and previous sensor readings.
    - use_any: logic op，True for OR，False for AND
    - args: Additional positional arguments to pass to the sensor_update function.
    - kwargs: Additional keyword arguments to pass to the sensor_update function.

    Returns:
    - A watcher function that returns True if the sensor readings have changed within the specified limits,
    False otherwise.
    """

    # Create a new buffer for the current sensor updates
    buffer_id = BufferRegistry.register_buffer()
    BufferRegistry.set_buffer(buffer_id, sensor_update(*args, **kwargs))

    logic_calc_func = any if use_any else all
    # Define the watcher function based on the provided limits
    if max_line and min_line:
        def _watcher() -> bool:
            nonlocal buffer_id
            update = sensor_update(*args, **kwargs)
            b = logic_calc_func(
                ((max_line > abs(update[x]) - BufferRegistry.get_buffer(buffer_id)[x]) > min_line) for x in sensor_id)
            BufferRegistry.set_buffer(buffer_id, update)
            return b
    elif min_line:
        def _watcher() -> bool:
            nonlocal buffer_id
            update = sensor_update(*args, **kwargs)
            b = logic_calc_func(
                (abs(update[x] - BufferRegistry.get_buffer(buffer_id)[x]) > min_line) for x in sensor_id)
            BufferRegistry.set_buffer(buffer_id, update)
            return b
    else:
        def _watcher() -> bool:
            nonlocal buffer_id
            update = sensor_update(*args, **kwargs)
            b = logic_calc_func(
                (abs(update[x] - BufferRegistry.get_buffer(buffer_id)[x]) < max_line) for x in sensor_id)
            BufferRegistry.set_buffer(buffer_id, update)
            return b

    return _watcher


def build_delta_watcher_full_ctrl(sensor_update: Callable[..., Sequence[Any]],
                                  sensor_ids: Tuple[int, ...],
                                  min_lines: Sequence[Optional[int]] = None,
                                  max_lines: Sequence[Optional[int]] = None,
                                  use_any: bool = False,
                                  args: Tuple = (),
                                  kwargs: Dict[str, Any] = {}) -> Watcher:
    """
      Build a delta watcher function that checks for changes in sensor readings.

      Args:
      - sensor_update: A function that retrieves the latest sensor readings.
      - sensor_ids: A tuple of indices representing the sensor values to monitor for changes.
      - min_lines: A sequence of minimum difference required between the current and previous sensor readings.
      - max_lines: A sequence of maximum difference allowed between the current and previous sensor readings.
      - use_any: logic op，True for OR，False for AND
      - args: Additional positional arguments to pass to the sensor_update function.
      - kwargs: Additional keyword arguments to pass to the sensor_update function.

      Returns:
      - A watcher function that returns True if the sensor readings have changed within the specified limits,
      False otherwise.
      """
    # Create a new buffer for the current sensor updates
    buffer_id = BufferRegistry.register_buffer()
    BufferRegistry.set_buffer(buffer_id, sensor_update(*args, **kwargs))

    belt_pass_sensors, high_pass_sensors, low_pass_sensors = sort_with_mode(max_lines, min_lines, sensor_ids)
    logic_calc_func = any if use_any else all
    parts = []
    if belt_pass_sensors:
        parts.append(
            lambda update, history: logic_calc_func(
                x[1] < abs(update[x[0]] - history[x[0]]) < x[2] for x in belt_pass_sensors))
    if high_pass_sensors:
        parts.append(lambda update, history: logic_calc_func(
            x[1] < abs(update[x[0]] - history[x[0]]) for x in high_pass_sensors))
    if low_pass_sensors:
        parts.append(
            lambda update, history: logic_calc_func(x[1] > abs(update[x[0]] - history[x[0]]) for x in low_pass_sensors))

    def assembly_watcher() -> bool:
        f"""
        a delta watcher function that checks for changes in sensor readings.
        Returns: True if the sensor readings have changed within the specified limits, False otherwise.
        
        Notes: 
            parts parameters are as follows
            
            sensor_id: {sensor_ids}
            min_line: {min_lines}
            max_line: {max_lines}
        """
        nonlocal buffer_id
        update = sensor_update(*args, **kwargs)
        b = logic_calc_func(part(update, BufferRegistry.get_buffer(buffer_id)) for part in parts)
        BufferRegistry.set_buffer(buffer_id, update)
        return b

    return assembly_watcher


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
