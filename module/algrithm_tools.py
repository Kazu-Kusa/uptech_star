import time
import timeit
import warnings
from random import choice
from typing import List, Union, Sequence, Tuple, Any

from .db_tools import persistent_lru_cache, CacheFILE
from ..constant import ENV_CACHE_DIR_PATH
import os
import numpy as np

cache_dir = os.environ.get(ENV_CACHE_DIR_PATH)


class MovingAverage:
    def __init__(self, size: int):
        self.queue = np.zeros(size)  # 定义队列
        self.current_size: int = 0  # 记录有效元素个数

    def next(self, val: float) -> float:
        if self.current_size < len(self.queue):
            self.current_size += 1

        self.queue[:-1] = self.queue[1:]  # 将队列往前移动
        self.queue[-1] = val  # 将最新的值添加到队列中

        return self.queue.sum() / self.current_size  # 计算滑动窗口范围内的平均值


@persistent_lru_cache(f'{cache_dir}/compute_relative_error_cache')
def compute_relative_error(current_angle: int, target_angle: int) -> List[int]:
    """
        计算当前角度与目标角度之间相对角度误差
        :param current_angle: 当前角度，取值范围[-180, 180]
        :param target_angle: 目标角度，取值范围[-180, 180]
        :return: 返回一个列表，第一位是需要顺时针旋转的角度值，第二位是需要逆时针旋转的角度值
        """
    ab_dst = abs(current_angle - target_angle)  # 绝对角度差
    if current_angle > target_angle:
        return [360 - ab_dst, -ab_dst]
    else:
        return [ab_dst, ab_dst - 360]


@persistent_lru_cache(f'{cache_dir}/compute_inferior_arc_cache')
def compute_inferior_arc(current_angle: int, target_angle: int) -> int:
    """
    计算当前角度到目标角度的顺时针方向和逆时针方向之间的较小夹角
    顺时针转动是+
    你是正转动是-
    :param current_angle: 当前角度，取值范围[-180, 180]
    :param target_angle: 目标角度，取值范围[-180, 180]
    :return: 返回值代表着沿着箭头前进从当前角度到目标角度最短的路径经过的弧度
    """
    ab_dst = abs(current_angle - target_angle)  # 找出两个角度差值的绝对值
    if ab_dst > 180:
        # 绝对角度差是优弧
        if current_angle > target_angle:
            return 360 - ab_dst  # 需要顺时针转动劣弧的距离
        else:
            return ab_dst - 360  # 需要逆时针转动劣弧的距离
    else:
        # 绝对角度差是劣弧
        if current_angle > target_angle:
            return -ab_dst  # 需要逆时针转动劣弧的距离
        else:
            return ab_dst  # 需要顺时针转动劣弧的距离


@persistent_lru_cache(f'{cache_dir}/calculate_relative_angle_cache')
def calculate_relative_angle(current_angle: int, offset_angle: int) -> int:
    """
    计算相对偏移特定角度之后的目标角度，返回值范围 [-180, 180]。
    :param current_angle: 当前角度，单位：度数。取值范围 [-180, 180]
    :param offset_angle: 偏移角度，单位：度数。
    :return: 偏移后的目标角度，单位：度数。取值范围 [-180, 180]
    """
    return (current_angle + offset_angle + 180) % 360 - 180


def bake_to_cache():
    """
    used to bake the cache
    :return:
    """
    start_time = time.time()
    for current_angle in range(-180, 180):
        print(f'baking {current_angle}')
        for target_angle in range(-180, 180):
            compute_inferior_arc(current_angle, target_angle)
            calculate_relative_angle(current_angle, target_angle)
            compute_relative_error(current_angle, target_angle)
    print(f'Build complete, cost {time.time() - start_time:.6f} s')
    warnings.warn('Saving to cache')
    CacheFILE.save_all_cache()


def performance_evaluate():
    def test():

        for current_angle in range(-180, 180):
            for target_angle in range(-180, 180):
                compute_inferior_arc(current_angle, target_angle)
                calculate_relative_angle(current_angle, target_angle)
                compute_relative_error(current_angle, target_angle)

    print(timeit.timeit(stmt=test, number=1))


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


def calc_p2p_dst(point_1: Tuple[int | float, int | float], point_2: Tuple[int | float, int | float]) -> float:
    return ((point_1[0] - point_2[0]) ** 2 + (
            point_1[1] - point_2[1]) ** 2) ** 0.5


def calc_p2p_error(start: Tuple[int | float, int | float], target: Tuple[int | float, int | float]) -> Tuple:
    return tuple(y - x for x, y in zip(start, target))
