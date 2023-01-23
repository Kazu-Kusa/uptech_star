#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Disable
import os
import sys
import threading
import time

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

    def __init__(self):
        # call father class init
        super(UpTech, self).__init__()
        super(CloseLoopController, self).__init__()
        self.LCD_Open(2)
        open_flag = self.ADC_IO_Open()
        print("ad_io_open = {}".format(open_flag))
        self.CDS_Open()
        self.cmd = 0
        self.adc_data = []
        self.io_data = []

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

    def edge_detect_thread(self):
        while True:
            self.adc_data = self.ADC_Get_All_Channel()
            io_all_input = self.ADC_IO_GetAllInputLevel()
            # convert all iolevel to a string
            io_array = '{:08b}'.format(io_all_input)
            self.io_data.clear()
            for index, value in enumerate(io_array):
                io_value = int(value)
                self.io_data.insert(0, io_value)

    def set_chassis_mode(self, mode):
        self.chassis_mode = mode

    def send_cmd(self):
        while True:
            if self.cmd == self.MOVE_UP:
                self.move_up()
            if self.cmd == self.MOVE_LEFT:
                self.move_left()
            if self.cmd == self.MOVE_RIGHT:
                self.move_right()
            if self.cmd == self.MOVE_YAW_LEFT:
                self.move_yaw_left()
            if self.cmd == self.MOVE_YAW_RIGHT:
                self.move_yaw_right()
            if self.cmd == self.MOVE_STOP:
                self.move_stop()
            if self.cmd == self.PICK_UP_BALL:
                self.pick_up_ball()

    """
    # 速度指令，自由控制-开环控制器
    def move_cmd(self, left_speed, right_speed):
        self.CDS_SetSpeed(1, left_speed)
        self.CDS_SetSpeed(2, -right_speed)
        self.CDS_SetSpeed(3, left_speed)
        self.CDS_SetSpeed(4, -right_speed)
    #  速度指令，闭环控制器，使用闭环控制时替换开环控制代码
    """

    def move_cmd(self, left_speed, right_speed, print_log=False):
        def move():
            self.set_motor_speed(1, -left_speed)
            self.set_motor_speed(2, right_speed)
            self.set_motor_speed(3, -left_speed)
            self.set_motor_speed(4, right_speed)

        if print_log:
            move()
        else:
            self.block_print()
            move()
            self.enable_print()

    def move_up(self):
        if self.chassis_mode == self.CHASSIS_MODE_SERVO:
            self.CDS_SetSpeed(1, self.SPEED)
            self.CDS_SetSpeed(2, self.SPEED)
            self.CDS_SetSpeed(3, self.SPEED)
            self.CDS_SetSpeed(4, self.SPEED)

        if self.chassis_mode == self.CHASSIS_MODE_CONTROLLER:
            self.CDS_SetSpeed(1, self.SPEED)
            self.CDS_SetSpeed(2, -self.SPEED + 10)

        self.cmd = self.NO_CONTROLLER

    def move_left(self):
        if self.chassis_mode == self.CHASSIS_MODE_SERVO:
            self.CDS_SetSpeed(1, -self.SPEED)
            self.CDS_SetSpeed(2, -self.SPEED)
            self.CDS_SetSpeed(3, self.SPEED)
            self.CDS_SetSpeed(4, self.SPEED)

        if self.chassis_mode == self.CHASSIS_MODE_CONTROLLER:
            self.CDS_SetSpeed(1, 156)
            self.CDS_SetSpeed(2, -200)
        self.cmd = self.NO_CONTROLLER

    def move_right(self):
        if self.chassis_mode == self.CHASSIS_MODE_SERVO:
            self.CDS_SetSpeed(1, self.SPEED)
            self.CDS_SetSpeed(2, self.SPEED)
            self.CDS_SetSpeed(3, -self.SPEED)
            self.CDS_SetSpeed(4, -self.SPEED)

        if self.chassis_mode == self.CHASSIS_MODE_CONTROLLER:
            self.CDS_SetSpeed(1, 200)
            self.CDS_SetSpeed(2, -156)
        self.cmd = self.NO_CONTROLLER

    def move_yaw_left(self):
        if self.chassis_mode == self.CHASSIS_MODE_SERVO:
            self.CDS_SetSpeed(1, -self.SPEED)
            self.CDS_SetSpeed(2, self.SPEED)
            self.CDS_SetSpeed(3, -self.SPEED)
            self.CDS_SetSpeed(4, self.SPEED)

        if self.chassis_mode == self.CHASSIS_MODE_CONTROLLER:
            self.CDS_SetSpeed(1, -self.YAW_SPEED)
            self.CDS_SetSpeed(2, -self.YAW_SPEED)
        self.cmd = self.NO_CONTROLLER

    def move_yaw_right(self):
        if self.chassis_mode == self.CHASSIS_MODE_SERVO:
            self.CDS_SetSpeed(1, -self.SPEED)
            self.CDS_SetSpeed(2, self.SPEED)
            self.CDS_SetSpeed(3, -self.SPEED)
            self.CDS_SetSpeed(4, self.SPEED)

        if self.chassis_mode == self.CHASSIS_MODE_CONTROLLER:
            self.CDS_SetSpeed(1, self.YAW_SPEED)
            self.CDS_SetSpeed(2, self.YAW_SPEED)
        self.cmd = self.NO_CONTROLLER

    def move_stop(self):
        self.CDS_SetSpeed(1, 0)
        self.CDS_SetSpeed(2, 0)
        self.CDS_SetSpeed(3, 0)
        self.CDS_SetSpeed(4, 0)
        self.cmd = self.NO_CONTROLLER

    def pick_up_ball(self):
        self.move_stop()
        time.sleep(2)
        self.CDS_SetAngle(5, 512, self.SPEED)
        time.sleep(2)
        self.CDS_SetAngle(6, 580, self.SPEED)
        self.CDS_SetAngle(7, 450, self.SPEED)
        time.sleep(2)
        self.CDS_SetAngle(5, 921, self.SPEED)
        time.sleep(2)
        self.CDS_SetAngle(6, 495, self.SPEED)
        self.CDS_SetAngle(7, 530, self.SPEED)
        self.cmd = self.NO_CONTROLLER

    def go_up_platform(self):
        self.move_up()
        time.sleep(1)
        self.CDS_SetAngle(5, 900, self.SPEED)
        self.CDS_SetAngle(6, 100, self.SPEED)
        time.sleep(3)
        self.CDS_SetAngle(5, 512, self.SPEED)
        self.CDS_SetAngle(6, 512, self.SPEED)
        time.sleep(2)
        self.CDS_SetAngle(7, 100, self.SPEED)
        self.CDS_SetAngle(8, 900, self.SPEED)
        time.sleep(2)
        time.sleep(1)
        self.CDS_SetAngle(7, 512, self.SPEED)
        self.CDS_SetAngle(8, 512, self.SPEED)
        # self.CDS_SetAngle(9,500,self.SPEED * 3)

    def servo_reset(self):
        self.CDS_SetAngle(5, 512, self.SPEED)
        self.CDS_SetAngle(6, 512, self.SPEED)
        self.CDS_SetAngle(7, 512, self.SPEED)
        self.CDS_SetAngle(8, 512, self.SPEED)

    def set_cds_mode(self, ids, mode):
        for id in ids:
            self.CDS_SetMode(id, mode)

    def set_controller_cmd(self, cmd):
        self.cmd = cmd

    def lcd_display(self, content):
        self.LCD_PutString(30, 0, content)
        self.LCD_Refresh()
        self.LCD_SetFont(self.FONT_8X14)


if __name__ == '__main__':
    # up_controller = UpController()
    # ids = [1,2]
    # servoids = [5,6,7,8]
    # up_controller.set_chassis_mode(up_controller.CHASSIS_MODE_CONTROLLER)
    # up_controller.set_cds_mode(ids,1)
    # up_controller.set_cds_mode(servoids,0)
    # # up_controller.go_up_platform()
    # up_controller.servo_reset()
    # up_controller.open_adc_io_update_thread()
    b = int("0x0b", 16)
    c = '{:08b}'.format(b)
    print(c)
