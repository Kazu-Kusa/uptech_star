import os
import time
import warnings
from typing import List

from ..constant import ENV_CACHE_DIR_PATH
from .db_tools import persistent_cache, CacheFILE

ANGLE_RESOLUTION: int = 100
FULL_ARC_ANGLE: int = 360 * ANGLE_RESOLUTION
HALF_ARC_ANGLE: int = int(FULL_ARC_ANGLE / 2)
cache_dir = os.environ.get(ENV_CACHE_DIR_PATH)


def is_tilted(roll: float, pitch: float, threshold=45 * ANGLE_RESOLUTION):
    """
    判断当前姿态是否倾倒

    :param roll: 横滚角，单位为度
    :param pitch: 俯仰角，单位为度
    :param threshold: 倾倒阈值，超过此角度则判断为倾倒，默认为45度
    :return: True代表倾倒，False代表未倾倒
    """
    return abs(roll) > threshold or abs(pitch) > threshold


@persistent_cache(f'{cache_dir}/compute_relative_error_cache')
def compute_relative_error(current_angle: int, target_angle: int) -> List[int]:
    """
        计算当前角度与目标角度之间相对角度误差
        :param current_angle: 当前角度，取值范围[-180, 180]
        :param target_angle: 目标角度，取值范围[-180, 180]
        :return: 返回一个列表，第一位是需要顺时针旋转的角度值，第二位是需要逆时针旋转的角度值
        """
    ab_dst = abs(current_angle - target_angle)  # 绝对角度差
    if current_angle > target_angle:
        return [FULL_ARC_ANGLE - ab_dst, -ab_dst]
    else:
        return [ab_dst, ab_dst - FULL_ARC_ANGLE]


@persistent_cache(f'{cache_dir}/compute_inferior_arc_cache')
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
    if ab_dst > HALF_ARC_ANGLE:
        # 绝对角度差是优弧
        if current_angle > target_angle:
            return FULL_ARC_ANGLE - ab_dst  # 需要顺时针转动劣弧的距离
        else:
            return ab_dst - FULL_ARC_ANGLE  # 需要逆时针转动劣弧的距离
    else:
        # 绝对角度差是劣弧
        if current_angle > target_angle:
            return -ab_dst  # 需要逆时针转动劣弧的距离
        else:
            return ab_dst  # 需要顺时针转动劣弧的距离


@persistent_cache(f'{cache_dir}/calculate_relative_angle_cache')
def calculate_relative_angle(current_angle: int, offset_angle: int) -> int:
    """
    计算相对偏移特定角度之后的目标角度，返回值范围 [-180, 180]。
    :param current_angle: 当前角度，单位：度数。取值范围 [-180, 180]
    :param offset_angle: 偏移角度，单位：度数。
    :return: 偏移后的目标角度，单位：度数。取值范围 [-180, 180]
    """
    return (current_angle + offset_angle + HALF_ARC_ANGLE) % FULL_ARC_ANGLE - HALF_ARC_ANGLE


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
    def test_lr():

        for current_angle in range(-180, 180):
            for target_angle in range(-180, 180):
                compute_inferior_arc(current_angle, target_angle)
                calculate_relative_angle(current_angle, target_angle)
                compute_relative_error(current_angle, target_angle)

    def run(func, ct=1):
        res_list = []
        for _ in range(ct):
            start = time.perf_counter_ns()
            func()
            end = time.perf_counter_ns()
            res_list.append((end - start) / 1000000)
        return res_list

    print(f'test: {run(test_lr)}')
