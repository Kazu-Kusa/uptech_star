from time import perf_counter


def delay_ms(milliseconds: int):
    start = perf_counter()
    while True:
        elapsed = (perf_counter() - start) * 1000
        if elapsed > milliseconds:
            break


def delay_us(microseconds: int):
    start = perf_counter()
    while True:
        elapsed = (perf_counter() - start) * 1000000
        if elapsed > microseconds:
            break
