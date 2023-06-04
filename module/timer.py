from time import perf_counter_ns

from time import perf_counter_ns


def delay_ms(milliseconds: int):
    end = perf_counter_ns() + milliseconds * 1000000
    while perf_counter_ns() < end:
        pass


def delay_us(microseconds: int):
    end = perf_counter_ns() + microseconds * 1000
    while perf_counter_ns() < end:
        pass


def current_ms():
    return int(perf_counter_ns() / 1000000)


def get_end_time_ms(milliseconds: int) -> int:
    return perf_counter_ns() + milliseconds * 1000000
