#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# import numpy as np
import ctypes
# from ctypes import *
# import numpy as np
from ctypes import cdll

import pigpio

__version__ = "1.0"
# hPi=pigpio.pi()
# #hPi=pigpio.pi()
# hSpi0=-1
# hSpi1=-1

FAN_GPIO_PWM = 18

so_up = cdll.LoadLibrary("libuptech.so")


class UpTech:
    CDS_MODE_SERVO = 0
    CDS_MODE_MOTOR = 1

    FONT_4X6 = 0
    FONT_5X8 = 1
    FONT_5X12 = 2
    FONT_6X8 = 3
    FONT_6X10 = 4
    FONT_7X12 = 5
    FONT_8X8 = 6
    FONT_8X12 = 7
    FONT_8X14 = 8
    FONT_10X16 = 9
    FONT_12X16 = 10
    FONT_12X20 = 11
    FONT_16X26 = 12
    FONT_22X36 = 13
    FONT_24X40 = 14

    COLOR_WHITE = 0xFFFF
    COLOR_BLACK = 0x0000
    COLOR_BLUE = 0x001F
    COLOR_BRED = 0XF81F
    COLOR_GRED = 0XFFE0
    COLOR_GBLUE = 0X07FF
    COLOR_RED = 0xF800
    COLOR_MAGENTA = 0xF81F
    COLOR_GREEN = 0x07E0
    COLOR_CYAN = 0x7FFF
    COLOR_YELLOW = 0xFFE0
    COLOR_BROWN = 0XBC40
    COLOR_BRRED = 0XFC07
    COLOR_GRAY = 0X8430
    COLOR_DARKBLUE = 0X01CF
    COLOR_LIGHTBLUE = 0X7D7C
    COLOR_GRAYBLUE = 0X5458
    COLOR_LIGHTGREEN = 0X841F
    COLOR_LGRAY = 0XC618
    COLOR_LGRAYBLUE = 0XA651
    COLOR_LBBLUE = 0X2B12

    __adc_data = ctypes.c_uint16 * 10
    __ADC_DATA = __adc_data()
    ADC_DATA = [0] * 10

    __mpu_float = ctypes.c_float * 3
    __MPU_DATA = __mpu_float()
    ACCEL_DATA = [0] * 3
    GYRO_DATA = [0] * 3
    ATTITUDE = [0] * 3

    def __init__(self):

        pigpio.exceptions = False
        self.hPi = pigpio.pi()
        assert not self.hPi.connected, 'pi is not connected'

        # self.hSpi1 = self.hPi.spi_open(2, 1000000, (1<<8)|(0<<0))
        # if self.hSpi1 < 0:
        #     self.hPi.spi_close(1)
        #     self.hSpi1 = self.hPi.spi_open(2, 1000000, (1<<8)|(0<<0))
        # pigpio.exceptions = True
        self.hPi.hardware_PWM(FAN_GPIO_PWM, 20000, 1000000)
        self.hPi.set_PWM_range(FAN_GPIO_PWM, 100)

    def FAN_Set_Speed(self, speed):
        if self.hPi >= 0:
            if speed > 100:
                speed = 100
            elif speed < 0:
                speed = 0
            self.hPi.set_PWM_dutycycle(FAN_GPIO_PWM, speed)

    @staticmethod
    def ADC_IO_Open():
        return so_up.adc_io_open()

    @staticmethod
    def ADC_IO_Close():
        so_up.adc_io_close()

    def ADC_Get_All_Channle(self):

        so_up.ADC_GetAll(self.__ADC_DATA)
        for i in range(10):
            self.ADC_DATA[i] = self.__ADC_DATA[i]
        # print self.ADC_DATA
        return self.ADC_DATA

    @staticmethod
    def ADC_Led_SetColor(index, RGB):
        so_up.adc_led_set(index, RGB)

    @staticmethod
    def ADC_IO_SetIOLevel(index, level):
        so_up.adc_io_Set(index, level)

    @staticmethod
    def ADC_IO_SetAllIOLevel(value):
        so_up.adc_io_SetAll(value)

    @staticmethod
    def ADC_IO_SetAllIOMode(mode):
        so_up.adc_io_ModeSetAll(mode)

    @staticmethod
    def ADC_IO_SetIOMode(index, mode):
        so_up.adc_io_ModeSet(index, mode)

    @staticmethod
    def ADC_IO_GetAllInputLevel():
        return so_up.adc_io_InputGetAll()

    @staticmethod
    def CDS_Open():
        so_up.cds_servo_open()

    @staticmethod
    def CDS_Close():
        so_up.cds_servo_close()

    @staticmethod
    def CDS_SetMode(id, mode):
        so_up.cds_servo_SetMode(id, mode)

    @staticmethod
    def CDS_SetAngle(id, angle, speed):
        so_up.cds_servo_SetAngle(id, angle, speed)

    @staticmethod
    def CDS_SetSpeed(id, speed):
        so_up.cds_servo_SetSpeed(id, speed)

    @staticmethod
    def CDS_GetCurPos(id):
        return so_up.cds_servo_GetPos(id)

    @staticmethod
    def MPU6500_Open():
        so_up.mpu6500_dmp_init()

    def MPU6500_GetAccel(self):
        so_up.mpu6500_Get_Accel(self.__MPU_DATA)
        for i in range(3):
            self.ACCEL_DATA[i] = self.__MPU_DATA[i]
        return self.ACCEL_DATA

    def MPU6500_GetGyro(self):
        so_up.mpu6500_Get_Gyro(self.__MPU_DATA)
        for i in range(3):
            self.GYRO_DATA[i] = self.__MPU_DATA[i]
        return self.GYRO_DATA

    def MPU6500_GetAttitude(self):
        so_up.mpu6500_Get_Attitude(self.__MPU_DATA)
        for i in range(3):
            self.ATTITUDE[i] = self.__MPU_DATA[i]
        return self.ATTITUDE

    @staticmethod
    def LCD_Open(dir):
        return so_up.lcd_open(dir)

    @staticmethod
    def LCD_Refresh():
        so_up.LCD_Refresh()

    @staticmethod
    def LCD_SetFont(font_index):
        so_up.LCD_SetFont(font_index)

    @staticmethod
    def LCD_SetForeColor(color):
        so_up.UG_SetForecolor(color)

    @staticmethod
    def LCD_SetBackColor(color):
        so_up.UG_SetBackcolor(color)

    @staticmethod
    def LCD_FillScreen(color):
        so_up.UG_FillScreen(color)

    @staticmethod
    def LCD_PutString(x, y, str):
        byte = ctypes.c_byte * len(str)
        bin = byte()
        i = 0
        for c in str:
            bin[i] = ord(c)
            i += 1
        so_up.UG_PutString(x, y, bin)

    @staticmethod
    def LCD_FillFrame(x1, y1, x2, y2, color):
        so_up.UG_FillFrame(x1, y1, x2, y2, color)

    @staticmethod
    def LCD_FillRoundFrame(x1, y1, x2, y2, r, color):
        so_up.UG_FillRoundFrame(x1, y1, x2, y2, r, color)

    @staticmethod
    def LCD_DrawMesh(x1, y1, x2, y2, color):
        so_up.UG_DrawMesh(x1, y1, x2, y2, color)

    @staticmethod
    def LCD_DrawFrame(x1, y1, x2, y2, color):
        so_up.UG_DrawFrame(x1, y1, x2, y2, color)

    @staticmethod
    def LCD_DrawRoundFrame(x1, y1, x2, y2, r, color):
        so_up.UG_DrawRoundFrame(x1, y1, x2, y2, r, color)

    @staticmethod
    def LCD_DrawPixel(x0, y0, color):
        so_up.UG_DrawPixel(x0, y0, color)

    @staticmethod
    def LCD_DrawCircle(x0, y0, r, color):
        so_up.UG_DrawCircle(x0, y0, r, color)

    @staticmethod
    def LCD_FillCircle(x0, y0, r, color):
        so_up.UG_FillCircle(x0, y0, r, color)

    @staticmethod
    def LCD_DrawArc(x0, y0, r, s, color):
        so_up.UG_DrawArc(x0, y0, r, s, color)

    @staticmethod
    def LCD_DrawLine(x1, y1, x2, y2, color):
        so_up.UG_DrawLine(x1, y1, x2, y2, color)
        # void UG_DrawArc( UG_S16 x0, UG_S16 y0, UG_S16 r, UG_U8 s, UG_COLOR c );
    # void UG_DrawLine( UG_S16 x1, UG_S16 y1, UG_S16 x2, UG_S16 y2, UG_COLOR c );


if __name__ == "__main__":
    a = UpTech()
    print(so_up)
    pass
