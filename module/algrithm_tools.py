import random

import numpy as np


class MovingAverage:
    def __init__(self, size):
        self.queue = np.zeros(size)  # 定义队列
        self.current_size = 0  # 记录有效元素个数

    def next(self, val):
        if self.current_size < len(self.queue):
            self.current_size += 1

        self.queue[:-1] = self.queue[1:]  # 将队列往前移动
        self.queue[-1] = val  # 将最新的值添加到队列中

        return self.queue.sum() / self.current_size  # 计算滑动窗口范围内的平均值


def compute_relative_error(current_angle: float, target_angle: float) -> list[float]:
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


def compute_inferior_arc(current_angle: float, target_angle: float) -> float:
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


def calculate_relative_angle(current_angle: float, offset_angle: float) -> float:
    """
    计算相对偏移特定角度之后的目标角度，返回值范围 [-180, 180]。
    :param current_angle: 当前角度，单位：度数。取值范围 [-180, 180]
    :param offset_angle: 偏移角度，单位：度数。
    :return: 偏移后的目标角度，单位：度数。取值范围 [-180, 180]
    """
    return (current_angle + offset_angle + 180) % 360 - 180


def determine_direction(current_angle: float, target_angle: float) -> int:
    """
    判断当前角度移动到目标角度是逆时针更近还是顺时针更近。
    :param current_angle: 当前角度，单位：度数。取值范围 [-180, 180]
    :param target_angle: 目标角度，单位：度数。取值范围 [-180, 180]
    :return: 若逆时针更近，则返回 -1；若顺时针更近，则返回 1；若两者距离相等，会返回-1。
    """
    angle_diff = (target_angle - current_angle + 180) % 360 - 180
    return int(angle_diff / abs(angle_diff))
