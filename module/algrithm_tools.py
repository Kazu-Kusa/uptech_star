from abc import ABC, abstractmethod
from random import choice
from typing import Union, Sequence, Tuple, List

from numpy import zeros, average


class BaseFilter(ABC):

    @abstractmethod
    def apply(self, value: float) -> float:
        pass


class MovingAverage(BaseFilter):

    def apply(self, value: float) -> float:
        self.queue[:-1] = self.queue[1:]  # 将队列往前移动
        self.queue[-1] = value  # 将最新的值添加到队列中
        # 计算滑动窗口范围内的平均值
        return average(self.queue)

    def __init__(self, size: int):
        self.queue = zeros(size)  # 定义队列


class AmplitudeLimitFilter(BaseFilter):
    def __init__(self, origin_filter: BaseFilter, limit: float):
        self.filter = origin_filter
        self.limit = limit

    def apply(self, value: float) -> float:
        filtered_value = self.filter.apply(value)
        return max(min(filtered_value, self.limit), -self.limit)


class WindowPredictorBase(ABC):

    @abstractmethod
    def predict(self, data: List[Union[float, int]]) -> List[Union[float, int]]:
        """
        Use the new input data to update the window
        then use all the data in the window to predict the next frame of data
        Args:
            data: the given data, which is a list, meaning a bunch of data read at the same time

        Returns:
            List[Union[float, int]]: the predicted data

        """
        pass

    def __init__(self, window_size: int):
        """
        Initialize the WindowPredictor.
        Args:
            window_size: the size of the window
        """
        self.window_size = window_size

        # init the window that contains the last window_size data
        self.window: List[Sequence[Union[float, int]]] = [[]] * window_size


def list_multiply(list1: Sequence[Union[float, int]],
                  list2: Sequence[Union[float, int]],
                  ) -> Tuple[int, ...]:
    # 计算每个元素相乘的结果，并将其转换为整数
    return tuple(int(x * y) for x, y in zip(list1, list2))


def factor_list_multiply(factor: Union[float, int],
                         factor_list: Sequence[Union[float, int]]
                         ) -> Tuple[int, ...]:
    """
    计算每个元素相乘的结果，并将其转换为整数
    :param factor:
    :param factor_list:
    :return:
    """
    return tuple(int(factor * x) for x in factor_list)


def multiply(factor_1: Union[float, int], factor_2: Union[float, int]) -> int:
    return int(factor_2 * factor_1)


def random_sign() -> int:
    """
    Generate a random sign (-1 or 1).

    Returns:
        int: The randomly generated sign (-1 or 1).
    """
    return choice([-1, 1])


def enlarge_multiplier_l() -> float:
    """
    Generate a multiplier for enlargement in a lower range.

    Returns:
        float: The randomly generated multiplier for enlargement in a lower range.
    """
    return choice([1.25, 1.275, 1.3, 1.325, 1.35, 1.375, 1.4, 1.45, 1.5])


def enlarge_multiplier_ll() -> float:
    """
    Generate a multiplier for enlargement in a middle range.

    Returns:
        float: The randomly generated multiplier for enlargement in a middle range.
    """
    return choice([1.5, 1.525, 1.55, 1.575, 1.6, 1.625, 1.65, 1.7, 1.75])


def enlarge_multiplier_lll() -> float:
    """
    Generate a multiplier for enlargement in an upper range.

    Returns:
        float: The randomly generated multiplier for enlargement in an upper range.
    """
    return choice([1.75, 1.775, 1.8, 1.825, 1.85, 1.875, 1.9, 1.95, 2.0, 2.1, 2.2, 2.4])


def shrink_multiplier_l() -> float:
    """
    Generate a multiplier for shrinkage in a lower range.

    Returns:
        float: The randomly generated multiplier for shrinkage in a lower range.
    """
    return choice([0.65, 0.7, 0.725, 0.7375, 0.75, 0.7625, 0.775, 0.7875, 0.8])


def shrink_multiplier_ll() -> float:
    """
    Generate a multiplier for shrinkage in a middle range.

    Returns:
        float: The randomly generated multiplier for shrinkage in a middle range.
    """
    return choice([0.55, 0.6, 0.625, 0.65, 0.6625, 0.675, 0.6875, 0.7])


def shrink_multiplier_lll() -> float:
    """
    Generate a multiplier for shrinkage in an upper range.

    Returns:
        float: The randomly generated multiplier for shrinkage in an upper range.
    """
    return choice([0.40, 0.5, 0.525, 0.55, 0.5625, 0.575, 0.5875, 0.6])


def float_multiplier_middle() -> float:
    """
    Generate a float multiplier in a middle range.

    Returns:
        float: The randomly generated float multiplier in a middle range.
    """
    return choice([0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.17, 1.25])


def float_multiplier_lower() -> float:
    """
    Generate a float multiplier in a lower range.

    Returns:
        float: The randomly generated float multiplier in a lower range.
    """
    return choice([0.8, 0.825, 0.85, 0.875, 0.9, 0.925, 0.95, 1.0, 1.05, 1.08, 1.1])


def float_multiplier_upper() -> float:
    """
    Generate a float multiplier in an upper range.

    Returns:
        float: The randomly generated float multiplier in an upper range.
    """
    return choice([0.9, 0.925, 0.95, 1.0, 1.05, 1.08, 1.1, 1.17, 1.25])


def calc_p2p_dst(point_1: Tuple[int | float, int | float], point_2: Tuple[int | float, int | float]) -> float:
    return ((point_1[0] - point_2[0]) ** 2 + (
            point_1[1] - point_2[1]) ** 2) ** 0.5


def calc_p2p_error(start: Tuple[int | float, int | float], target: Tuple[int | float, int | float]) -> Tuple:
    return tuple(y - x for x, y in zip(start, target))
