from time import perf_counter_ns


def delay_ms(milliseconds: int):
    """

    :param milliseconds:
    :return:
    """
    start = perf_counter_ns()
    while True:
        elapsed = (perf_counter_ns() - start) // 1000000
        if elapsed > milliseconds:
            break


def delay_us(microseconds: int):
    """

    :param microseconds:
    :return:
    """
    start = perf_counter_ns()
    while True:
        elapsed = (perf_counter_ns() - start) // 1000
        if elapsed > microseconds:
            break
