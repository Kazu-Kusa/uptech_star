from time import perf_counter_ns
from typing import Callable, Tuple, Union, Dict, Sequence, Optional

from .timer import delay_us

FullUpdater = Callable[[], Sequence[Union[float, int]]]
IndexedUpdater = Callable[[int], Union[float, int]]
SensorUpdaters = Tuple[Optional[FullUpdater], Optional[IndexedUpdater]]
FU_INDEX = 0
IU_INDEX = 1


def default_full_updater() -> Sequence[Union[float, int]]:
    return [-1]


def default_indexed_updater(index: int) -> Union[float, int]:
    return -1


class SensorHub(object):
    ON_BOARD_ADC_ID = 0
    ON_BOARD_IO_ID = 1
    EXPANSION_ADC_ID = 2
    EXPANSION_IO_ID = 3

    def __init__(self,
                 on_board_adc_updater: SensorUpdaters,
                 on_board_io_updater: SensorUpdaters,
                 expansion_adc_updater: SensorUpdaters,
                 expansion_io_updater: SensorUpdaters
                 ):

        self._full_updaters = (
            on_board_adc_updater[FU_INDEX] if on_board_adc_updater[FU_INDEX] else default_full_updater,
            on_board_io_updater[FU_INDEX] if on_board_io_updater[FU_INDEX] else default_full_updater,
            expansion_adc_updater[FU_INDEX] if expansion_adc_updater[FU_INDEX] else default_full_updater,
            expansion_io_updater[FU_INDEX] if expansion_io_updater[FU_INDEX] else default_full_updater)
        self._updaters_validity_check(self._full_updaters)

        self._indexed_updaters = (
            on_board_adc_updater[IU_INDEX] if on_board_adc_updater[IU_INDEX] else default_indexed_updater,
            on_board_io_updater[IU_INDEX] if on_board_io_updater[IU_INDEX] else default_indexed_updater,
            expansion_adc_updater[IU_INDEX] if expansion_adc_updater[IU_INDEX] else default_indexed_updater,
            expansion_io_updater[IU_INDEX] if expansion_io_updater[IU_INDEX] else default_indexed_updater
        )
        self.on_board_adc_updater = on_board_adc_updater
        self.on_board_io_updater = on_board_io_updater
        self.expansion_adc_updater = expansion_adc_updater
        self.expansion_io_updater = expansion_io_updater

    def __str__(self):
        temp = 'Updaters:\n'
        for updater in self._full_updaters:
            temp += f'{updater}\n' \
                    f'\t\tSequenceLength: {len(updater())}\n' \
                    f'\t\tSequenceType: {type(updater()[0])}\n\n'
        return temp

    @property
    def updaters(self):
        return self._full_updaters, self._indexed_updaters

    @staticmethod
    def _updaters_validity_check(updaters: Sequence[FullUpdater]):
        if not all(updater() for updater in updaters):
            raise IndexError('Some of existing updaters are invalid, please check!')


class LocalFullUpdaterConstructor(object):

    @staticmethod
    def from_full_updater(full_updater: FullUpdater, sensor_ids: Sequence[int]) -> FullUpdater:
        def updater() -> Sequence[Union[float, int]]:
            return tuple(full_updater()[sensor_id] for sensor_id in sensor_ids)

        return updater

    @staticmethod
    def from_indexed_updater(indexed_updater: IndexedUpdater, sensor_ids: Sequence[int]) -> FullUpdater:
        def updater() -> Sequence[Union[float, int]]:
            return tuple(indexed_updater(sensor_id) for sensor_id in sensor_ids)

        return updater


def record_updater(updater: FullUpdater, duration: int, interval: int) -> Dict:
    result = []
    print(f"recording updaters: {updater}, duration: {duration} ms, interval: {interval} ms")
    end_time = perf_counter_ns() + duration * 1e6
    while perf_counter_ns() < end_time:
        delay_us(interval * 1000)
        result.append(list(updater()))
    return {f'{updater.__name__}-{duration}-{interval}': result}