import warnings
from time import perf_counter_ns

from time import perf_counter_ns
from typing import Callable


def delay_ms(milliseconds: int,
             breaker_func: Callable[[], bool] = None,
             break_action_func: Callable[[], None] = None) -> bool:
    """
    delay_ms 函数具有延迟指定毫秒数的功能，在提供退出条件和退出后执行操作时支持可选参数。

    如果给出了 breaker_func 参数，则在等待过程中每隔一段时间调用此函数检查是否应该中断等待，并执行相应的 break_action_func 应用程序进行清理或下一步操作。如果未提供 breaker_func，则函数将在指定的时间内阻塞线程并等待完成。

    当 breaker_func 返回 True 值时，函数将立即返回并触发 break_action_func。（如果可用）

    特别地，已更新代码中针对终止信号和退出处理的逻辑（调用 break 让循环直接退出）。
    :param milliseconds:
    :param breaker_func:
    :param break_action_func:
    :return:
    """

    def delay(millisecond: int) -> bool:
        end = perf_counter_ns() + millisecond * 1000000
        while perf_counter_ns() < end:
            pass
        return False

    def delay_with_breaker(millisecond: int,
                           breaker: Callable[[], bool],
                           break_action: Callable[[], None]) -> bool:
        end = perf_counter_ns() + millisecond * 1000000
        while perf_counter_ns() < end:
            if breaker():
                break_action()
                return True
        return False
        # add bool return to check the exit type

    if breaker_func and break_action_func:

        return delay_with_breaker(millisecond=milliseconds,
                                  breaker=breaker_func,
                                  break_action=break_action_func)
    elif breaker_func:
        return delay_with_breaker(millisecond=milliseconds,
                                  breaker=breaker_func,
                                  break_action=lambda: None)
    else:
        return delay(millisecond=milliseconds)


def delay_us(microseconds: int):
    end = perf_counter_ns() + microseconds * 1000
    while perf_counter_ns() < end:
        pass


def current_ms():
    return int(perf_counter_ns() / 1000000)


def get_end_time_ms(milliseconds: int) -> int:
    return perf_counter_ns() + milliseconds * 1000000
