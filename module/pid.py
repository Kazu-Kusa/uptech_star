import time
from typing import Callable
from time import perf_counter_ns

from .algrithm_tools import MovingAverage


def delay_ms(milliseconds: int):
    start = perf_counter_ns()
    while True:
        elapsed = (perf_counter_ns() - start) // 1000000
        if elapsed > milliseconds:
            break


# TODO: both PD and PID  are haven't react properly on direction change
def PD_control(controller_func: Callable[[int, int], None],
               evaluator_func: Callable[[], float],
               error_func: Callable[[float, float], float],
               target: float,
               Kp: float = 80, Kd: float = 16,
               cs_limit: float = 2000, target_tolerance: float = 15,
               smooth_window_size: int = 4):
    """
    PD controller designed to control the action-T using MPU-6500
    :param smooth_window_size:
    :param controller_func:
    :param evaluator_func:
    :param error_func:
    :param target:
    :param Kp:
    :param Kd:
    :param cs_limit:
    :param target_tolerance:
    :return:
    """

    last_state = evaluator_func()
    last_time = perf_counter_ns()
    current_error = error_func(last_state, target)

    if current_error < target_tolerance and Kp * current_error < cs_limit:
        # control strength is small and current state is near the target
        return

    slide_window = MovingAverage(smooth_window_size)

    while True:

        current_state_MA = slide_window.next(evaluator_func())
        current_time = perf_counter_ns()

        current_error = error_func(current_state_MA, target)

        d_target = (current_state_MA - last_state) / (current_time - last_time)

        control_strength = int(Kp * current_error + Kd * d_target)
        if abs(current_error) < target_tolerance and control_strength < cs_limit:
            controller_func(0, 0)
            break
        controller_func(control_strength, -control_strength)

        last_state = current_state_MA  # 更新前一个状态
        last_time = current_time  # 更新前一个时间


def PID_control(controller_func: Callable[[int, int], None],
                evaluator_func: Callable[[], float],
                error_func: Callable[[float, float], float],
                target: float,
                Kp: float = 80, Kd: float = 16, Ki: float = 2,
                cs_limit: float = 2000, target_tolerance: float = 15,
                smooth_window_size: int = 4, end_pause: bool = True, rip_round: int = 5, ):
    """
    PID controller designed to control the action-T using MPU-6500

    :param end_pause:
    :param delay:
    :param smooth_window_size:
    :param controller_func:
    :param evaluator_func:
    :param error_func:
    :param target:
    :param Kp:
    :param Kd:
    :param Ki:
    :param cs_limit:
    :param target_tolerance:
    :return:
    """

    last_state = evaluator_func()
    last_time = perf_counter_ns()
    current_error = error_func(last_state, target)

    if current_error < target_tolerance and Kp * current_error < cs_limit:
        # control strength is small and current state is near the target
        return
    slide_window = MovingAverage(smooth_window_size)
    i_error = 0
    ct = 0
    while True:
        current_state_MA = slide_window.next(evaluator_func())

        current_time = perf_counter_ns()

        current_error = error_func(current_state_MA, target)
        delta_time = current_time - last_time

        d_target = (current_state_MA - last_state) / delta_time
        i_error += current_error * delta_time

        kd_term = Kd * d_target
        ki_term = Ki * i_error
        Kp_term = Kp * current_error
        # print(f'Kp:{Kp_term}|Ki:{ki_term}|Kd:{kd_term}')
        control_strength = int(Kp_term + kd_term + ki_term)
        if abs(current_error) < target_tolerance and control_strength < cs_limit:

            if end_pause:
                controller_func(0, 0)
            break
        ct += 1
        if ct % rip_round == 0:
            ct = 0
            controller_func(control_strength, -control_strength)

        last_state = current_state_MA
        last_time = current_time
