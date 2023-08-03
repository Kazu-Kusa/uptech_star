from random import choice
from typing import Union, Sequence, Tuple
import numpy as np
from abc import ABC, abstractmethod


class BaseFilter(ABC):

    @abstractmethod
    def apply(self, value: float) -> float:
        pass


class MovingAverage(BaseFilter):
    
    def apply(self, value: float) -> float:
        self.queue[:-1] = self.queue[1:]  # 将队列往前移动
        self.queue[-1] = value  # 将最新的值添加到队列中
        # 计算滑动窗口范围内的平均值
        return np.average(self.queue)

    def __init__(self, size: int):
        self.queue = np.zeros(size)  # 定义队列


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
    return choice([-1, 1])


def random_enlarge_multiplier() -> float:
    return choice([1.50, 1.55, 1.60, 1.65, 1.70, 1.75, 1.80, 1.85, 1.90, 1.95, 2.00])


def random_shrink_multiplier() -> float:
    return choice([0.5, 0.525, 0.55, 0.575, 0.6, 0.625, 0.65, ])


def random_float_multiplier() -> float:
    return choice([0.75, 0.775, 0.8, 0.825, 0.85, 0.875, 0.9, 0.925, 0.95, 0.975,
                   1.0, 1.025, 1.05, 1.075, 1.1, 1.125, 1.15, 1.175, 1.2, 1.225, 1.25])


def calc_p2p_dst(point_1: Tuple[int | float, int | float], point_2: Tuple[int | float, int | float]) -> float:
    return ((point_1[0] - point_2[0]) ** 2 + (
            point_1[1] - point_2[1]) ** 2) ** 0.5


def calc_p2p_error(start: Tuple[int | float, int | float], target: Tuple[int | float, int | float]) -> Tuple:
    return tuple(y - x for x, y in zip(start, target))
