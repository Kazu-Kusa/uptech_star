from numba import njit
from time import perf_counter_ns


@njit(fastmath=True)
def delay_ms(milliseconds: int):
    start = perf_counter_ns()
    while True:
        elapsed = (perf_counter_ns() - start) // 1000000
        if elapsed > milliseconds:
            break


@njit(fastmath=True)
def delay_us(microseconds: int):
    start = perf_counter_ns()
    while True:
        elapsed = (perf_counter_ns() - start) // 1000
        if elapsed > microseconds:
            break
