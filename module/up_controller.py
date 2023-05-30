import os
import sys
import threading
import time
import warnings

from .close_loop_controller import CloseLoopController
from .uptech import UpTech


class UpController(UpTech, CloseLoopController):

    def __init__(self, debug: bool = False, using_updating_thread: bool = False, fan_control: bool = True):
        self.debug = debug
        # call father class init
        UpTech.__init__(self, debug=debug, fan_control=fan_control)
        CloseLoopController.__init__(self)

        # open the io-adc plug and print the returned log
        print(f"Sensor channel Init times: {self.ADC_IO_Open()}")
        if using_updating_thread:
            warnings.warn('opening sensors update thread')
            self.open_adc_io_update_thread()
        else:
            warnings.warn('NOT using sensors update thread')

    def open_adc_io_update_thread(self):
        """
        open data update thread
        """
        edge_thread = threading.Thread(name="adc_io_sync_thread", target=self.adc_io_sync_thread)
        edge_thread.daemon = True
        edge_thread.start()

        if self.debug:
            print('adc-io update thread started')

    def adc_io_sync_thread(self):
        """
        update data thread
        """
        while 1:
            self.adc_all = self.ADC_Get_All_Channel()
            self.io_all = [int(bit) for bit in f"{self.ADC_IO_GetAllInputLevel():08b}"]

    def move_cmd(self, left_speed, right_speed) -> None:
        """
        control the motor
        :param left_speed:
        :param right_speed:
        :return:
        """
        self.set_motors_speed([right_speed, right_speed, -left_speed, -left_speed], debug=self.debug)


def motor_speed_test(speed_level: int = 11, interval: float = 1, using_id: bool = True, laps: int = 3):
    """
    motor speed test function,used to test and check  if the driver configurations are correct
    :param speed_level:
    :param interval:
    :param using_id:
    :param laps:
    :return:
    """
    con = CloseLoopController()
    try:
        for _ in range(laps):
            if using_id:
                for i in range(speed_level):
                    print(f'doing {i * 1000}')
                    con.set_motors_speed([i * 1000] * 4)
                    time.sleep(interval)
            else:
                for i in range(speed_level):
                    print(f'doing {i * 1000}')
                    con.set_all_motors_speed(i * 1000)
                    time.sleep(interval)
    finally:
        con.set_all_motors_speed(0)
    print('over')


def motor_speed_test_liner(speed_level: int = 11, resolution: int = 10, detailed_info: bool = False,
                           using_id: bool = True, laps: int = 3):
    """
    motor speed test,but with fine precision,used to check accuracy
    :param speed_level:
    :param resolution:
    :param detailed_info:
    :param using_id:
    :param laps:
    :return:
    """

    con = UpController()

    try:
        for i in range(0, speed_level * 1000, resolution):
            con.set_motors_speed([i] * 4)
            if detailed_info:
                print(f'rising at {i}')
        for i in range(speed_level * 1000, 0, -resolution):
            con.set_motors_speed([i] * 4)
            if detailed_info:
                print(f'dropping at {i}')
    finally:
        con.set_all_motors_speed(0)
    print('over')
