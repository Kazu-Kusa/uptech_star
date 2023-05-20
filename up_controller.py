import os
import sys
import threading

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
        def move():
            self.set_motor_speed(1, left_speed)
            self.set_motor_speed(2, right_speed)
            self.set_motor_speed(3, -left_speed)
            self.set_motor_speed(4, -right_speed)

        if print_log:
            move()
        else:
            self.block_print()
            move()
            self.enable_print()

    def lcd_display(self, content):
        self.LCD_PutString(30, 0, content)
        self.LCD_Refresh()
        self.LCD_SetFontSize(self.FONT_8X14)


if __name__ == '__main__':
    pass
