from time import perf_counter_ns

from time import perf_counter_ns


def delay_ms(milliseconds: int):
    end = perf_counter_ns() + milliseconds * 1000000
    while perf_counter_ns() < end:
        pass


def delay_us(microseconds: int):
    end = perf_counter_ns() + microseconds * 1000000
    while perf_counter_ns() > end:
        pass
