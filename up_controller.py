import os
import sys
import threading

from .close_loop_controller import CloseLoopController
from .uptech import UpTech


class UpController(UpTech, CloseLoopController):
    # cmd
    NO_CONTROLLER = 0
    MOVE_UP = 1
    MOVE_LEFT = 2
    MOVE_RIGHT = 3
    MOVE_YAW_LEFT = 4
    MOVE_YAW_RIGHT = 5
    MOVE_STOP = 6
    PICK_UP_BALL = 7

    SPEED = 256
    YAW_SPEED = 210

    # GET_AD_DATA
    # chassis_mode 1 for servo ,2 for controller
    CHASSIS_MODE_SERVO = 1
    CHASSIS_MODE_CONTROLLER = 2

    def __init__(self, debug=False):
        self.chassis_mode = None
        self.debug = debug
        # call father class init
        UpTech.__init__(self)
        CloseLoopController.__init__(self)
        # set the display direction to Horizontal display
        self.LCD_Open(2)
        # open the io-adc plug and print the returned log
        print(f"ad_io_open_times: {self.ADC_IO_Open()}")

        self.cmd = 0

        self.open_adc_io_update_thread()

    def open_send_cmd_thread(self):
        controller_thread = threading.Thread(name="up_controller_thread", target=self.send_cmd)
        controller_thread.daemon = True
        controller_thread.start()

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
        edge_thread = threading.Thread(name="edge_detect_thread", target=self.edge_detect_thread)
        edge_thread.daemon = True
        edge_thread.start()

        if self.debug:
            print('adc-io update thread started')

    def edge_detect_thread(self):
        """
        update data thread
        """
        while 1:
            self.adc_all = self.ADC_Get_All_Channel()
            io_all_input = self.ADC_IO_GetAllInputLevel()
            # convert all io level to a string
            io_array = '{:08b}'.format(io_all_input)
            self.io_all = [int(x) for x in io_array]

    def set_chassis_mode(self, mode):
        self.chassis_mode = mode

    def move_cmd_open_loop(self, left_speed, right_speed):
        """
        # 速度指令，自由控制-开环控制器
        # 速度指令，闭环控制器，使用闭环控制时替换开环控制代码
        """
        self.CDS_SetSpeed(1, left_speed)
        self.CDS_SetSpeed(2, -right_speed)
        self.CDS_SetSpeed(3, left_speed)
        self.CDS_SetSpeed(4, -right_speed)

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
    up_controller = UpController()
    ids = [1, 2]

    up_controller.set_chassis_mode(up_controller.CHASSIS_MODE_CONTROLLER)
    up_controller.open_adc_io_update_thread()
    b = int("0x0b", 16)
    c = '{:08b}'.format(b)
    print(c)
