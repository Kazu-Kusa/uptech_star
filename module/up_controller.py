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
        CloseLoopController.__init__(self, debug=debug)

        # open the io-adc plug and print the returned log
        print(f"Sensor channel Init times: {self.ADC_IO_Open()}")
        if using_updating_thread:
            warnings.warn('opening sensors update thread')
            self.io_all_syncing = None
            self.adc_all_syncing = None
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
            self.adc_all_syncing = self.adc_all_channels
            self.io_all_syncing = self.io_all_channels

    def move_cmd(self, left_speed: int, right_speed: int) -> None:
        """
        control the motor
        :param left_speed:
        :param right_speed:
        :return:
        """
        if left_speed + right_speed == 0:
            self.set_all_motors_speed(right_speed)
            return
        self.set_motors_speed([right_speed, right_speed, -left_speed, -left_speed])


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
