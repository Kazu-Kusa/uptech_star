from time import perf_counter_ns
from typing import Callable, Tuple, Union, Dict, Sequence, Optional

from .timer import delay_us

Updater = Callable[[], Sequence[Union[float, int]]]


class SensorHub(object):
    ON_BOARD_ADC_ID = 0
    ON_BOARD_IO_ID = 1
    EXPANSION_ADC_ID = 2
    EXPANSION_IO_ID = 3

    def __init__(self,
                 on_board_adc_updater: Optional[Updater] = None,
                 on_board_io_updater: Optional[Updater] = None,
                 expansion_adc_updater: Optional[Updater] = None,
                 expansion_io_updater: Optional[Updater] = None
                 ):
        self._updaters = (on_board_adc_updater,
                          on_board_io_updater,
                          expansion_adc_updater,
                          expansion_io_updater)
        self._updaters_validity_check(self.updaters)

        self.on_board_adc_updater = on_board_adc_updater
        self.on_board_io_updater = on_board_io_updater
        self.expansion_adc_updater = expansion_adc_updater
        self.expansion_io_updater = expansion_io_updater

    def __str__(self):
        temp = 'Updaters:\n'
        for updater in self._updaters:
            temp += f'{updater}\n' \
                    f'\t\tSequenceLength: {len(updater())}\n' \
                    f'\t\tSequenceType: {type(updater()[0])}\n\n'
        return temp

    @property
    def updaters(self):
        return self._updaters

    @staticmethod
    def _updaters_validity_check(updaters: Sequence[Updater]):
        if not all(updater() for updater in updaters):
            raise IndexError('Some of existing updaters are invalid, please check!')

    def updater_constructor(self, sensor_ids: Tuple[Tuple[int, int], ...]) -> Updater:
        def updater() -> Sequence[Union[float, int]]:
            return [self._updaters[sensor_id[0]]()[sensor_id[1]] for sensor_id in sensor_ids]

        return updater


def record_updater(updater: Updater, duration: int, interval: int) -> Dict:
    result = []
    print(f"recording updaters: {updater}, duration: {duration} ms, interval: {interval} ms")
    end_time = perf_counter_ns() + duration * 1e6
    while perf_counter_ns() < end_time:
        delay_us(interval * 1000)
        result.append(list(updater()))
    return {f'{updater.__name__}-{duration}-{interval}': result}
