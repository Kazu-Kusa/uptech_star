from time import perf_counter_ns
from typing import Callable, Optional


def delay_ms(milliseconds: int,
             breaker_func: Optional[Callable[[], bool]] = None) -> int:
    """
    delay_ms 函数具有延迟指定毫秒数的功能，在提供退出条件和退出后执行操作时支持可选参数。
    如果给出了 breaker_func 参数，则在等待过程中每隔一段时间调用此函数检查是否应该中断等待
    :param milliseconds:
    :param breaker_func:
    :return:
    """

    def delay(millisecond: int) -> bool:
        end = perf_counter_ns() + millisecond * 1000000
        while perf_counter_ns() < end:
            pass
        return False

    def delay_with_breaker(millisecond: int,
                           breaker: Callable[[], bool]) -> bool:
        end = perf_counter_ns() + millisecond * 1000000
        while perf_counter_ns() < end:
            if breaker():
                return True
        return False
        # add bool return to check the exit type

    if breaker_func:
        return delay_with_breaker(millisecond=milliseconds,
                                  breaker=breaker_func)
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
