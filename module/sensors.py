from time import perf_counter_ns
from typing import Callable, Tuple, List, Union, Dict, Sequence

from .timer import delay_us

Updater = Callable[[], Sequence[Union[float, int]]]


class SensorHub(object):

    def __init__(self, updaters: Sequence[Updater]):
        self.updaters_validity_check(updaters)
        self._analog_updaters: Tuple[Updater, ...] = tuple(updaters)

    def __str__(self):
        temp = 'Updaters:\n'
        for updater in self._analog_updaters:
            temp += f'{updater}\n' \
                    f'\t\tSequenceLength: {len(updater())}\n' \
                    f'\t\tSequenceType: {type(updater()[0])}\n\n'
        return temp

    @property
    def updaters(self):
        return self._analog_updaters

    @staticmethod
    def updaters_validity_check(updaters: Sequence[Updater]):
        if not all(updater() for updater in updaters):
            raise IndexError('Some of existing updaters are invalid, please check!')

    def __getitem__(self, item: Union[Tuple[int, int], int]) -> Union[Union[float, int], List[Union[float, int]]]:
        if isinstance(item, int):
            return self._analog_updaters[item]()
        elif isinstance(item, Tuple):
            return self._analog_updaters[item[0]][item[1]]
        raise IndexError('Invalid index!')

    def updater_constructor(self, sensor_ids: Tuple[Tuple[int, int], ...]) -> Updater:
        def updater():
            return [self[i] for i in sensor_ids]

        return updater


def record_updater(updater: Updater, duration: int, interval: int) -> Dict:
    result = []
    print(f"recording updaters: {updater}, duration: {duration} ms, interval: {interval} ms")
    end_time = perf_counter_ns() + duration * 1e6
    while perf_counter_ns() < end_time:
        delay_us(interval * 1000)
        result.append(list(updater()))
    return {f'{updater.__name__}-{duration}-{interval}': result}
