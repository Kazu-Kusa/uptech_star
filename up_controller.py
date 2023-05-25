import os
import sys
import threading
import time

from .close_loop_controller import CloseLoopController
from .uptech import UpTech


class UpController(UpTech, CloseLoopController):

    def __init__(self, debug=False):
        self.debug = debug
        # call father class init
        UpTech.__init__(self)
        CloseLoopController.__init__(self)
        # set the display direction to Horizontal display
        self.LCD_Open()
        # open the io-adc plug and print the returned log
        print(f"ad_io_open_times: {self.ADC_IO_Open()}")

        self.open_adc_io_update_thread()

    @staticmethod
    def block_print():
        sys.stdout = open(os.devnull, 'w')

    # Restore
    @staticmethod
    def enable_print():
        sys.stdout = sys.__stdout__

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

    def move_cmd(self, left_speed, right_speed, print_log=False):

        if print_log:
            self.set_motors_speed([left_speed, right_speed, -left_speed, -right_speed])
        else:
            self.block_print()
            self.set_motors_speed([left_speed, right_speed, -left_speed, -right_speed])
            self.enable_print()

    def lcd_display(self, content):
        self.LCD_PutString(30, 0, content)
        self.LCD_Refresh()
        self.LCD_SetFontSize(self.FONT_8X14)


def motor_speed_test(speed_level: int = 11, using_id: bool = True, laps: int = 3):
    con = UpController()
    try:
        for _ in range(laps):
            if using_id:
                for i in range(speed_level):
                    print(f'doing {i * 1000}')
                    con.set_motors_speed([i * 1000] * 4)
                    time.sleep(1)
            else:
                for i in range(speed_level):
                    print(f'doing {i * 1000}')
                    con.set_all_motors_speed(i * 1000)
                    time.sleep(1)
    finally:
        con.set_all_motors_speed(0)
    print('over')


if __name__ == '__main__':
    pass
