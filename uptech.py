#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ctypes
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

    __mpu_float = ctypes.c_float * 3
    __MPU_DATA = __mpu_float()

    def __init__(self):
        pigpio.exceptions = False
        self.hPi = pigpio.pi()
        assert self.hPi.connected, 'pi is not connected'

        # self.hSpi1 = self.hPi.spi_open(2, 1000000, (1<<8)|(0<<0))
        # if self.hSpi1 < 0:
        #     self.hPi.spi_close(1)
        #     self.hSpi1 = self.hPi.spi_open(2, 1000000, (1<<8)|(0<<0))
        # pigpio.exceptions = True
        self.hPi.hardware_PWM(FAN_GPIO_PWM, 20000, 1000000)
        self.hPi.set_PWM_range(FAN_GPIO_PWM, 100)

    def FAN_Set_Speed(self, speed):
        self.hPi.set_PWM_dutycycle(FAN_GPIO_PWM, speed)

    @staticmethod
    def ADC_IO_Open():
        return so_up.adc_io_open()

    @staticmethod
    def ADC_IO_Close():
        so_up.adc_io_close()

    def ADC_Get_All_Channel(self):
        """
        get all adc channels and return they as a tuple
        """
        so_up.ADC_GetAll(self.__ADC_DATA)
        # return a tuple
        return self.__ADC_DATA,

    @staticmethod
    def ADC_Led_SetColor(index: int, color_intensity: int):
        """
        set the color of the LED according to index and color_intensity
        """
        so_up.adc_led_set(index, color_intensity)

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
        """
        get all io plug input level
        """
        return so_up.adc_io_InputGetAll()

    @staticmethod
    def CDS_Open():
        """
        open all servos
        """
        so_up.cds_servo_open()

    @staticmethod
    def CDS_Close():
        """
        close all servos
        """
        so_up.cds_servo_close()

    @staticmethod
    def CDS_SetMode(servos_id, mode):
        """
        set servos motion mode according to servos_id and mode
        """
        so_up.cds_servo_SetMode(servos_id, mode)

    @staticmethod
    def CDS_SetAngle(servos_id, angle, speed):
        so_up.cds_servo_SetAngle(servos_id, angle, speed)

    @staticmethod
    def CDS_SetSpeed(servos_id, speed):
        so_up.cds_servo_SetSpeed(servos_id, speed)

    @staticmethod
    def CDS_GetCurPos(servos_id):
        return so_up.cds_servo_GetPos(servos_id)

    @staticmethod
    def MPU6500_Open():
        """
        initialize the MPU6500
        default settings:
            acceleration: -+8G
            gyro: -+2000 degree/s
            sampling rate: 1kHz
        """
        so_up.mpu6500_dmp_init()

    def MPU6500_GetAccel(self):
        """
        get the acceleration from MPU6500
        """
        so_up.mpu6500_Get_Accel(self.__MPU_DATA)

        return self.__MPU_DATA,

    def MPU6500_GetGyro(self):
        """
        get gyro from MPU6500
        """
        so_up.mpu6500_Get_Gyro(self.__MPU_DATA)

        return self.__MPU_DATA,

    def MPU6500_GetAttitude(self):
        """
        get attitude from MPU6500

        """

        so_up.mpu6500_Get_Attitude(self.__MPU_DATA)

        return self.__MPU_DATA,

    @staticmethod
    def LCD_Open(direction: int):
        """
        set the LCD displaying direction

        1 for vertical, 2 for horizontal
        """
        assert direction == 1 or direction == 2, "1 for vertical and 2 for horizontal"

        return so_up.lcd_open(direction)

    @staticmethod
    def LCD_Refresh():
        so_up.LCD_Refresh()

    @staticmethod
    def LCD_SetFont(font_index: int):
        so_up.LCD_SetFont(font_index)

    @staticmethod
    def LCD_SetForeColor(color_intensity:int):
        so_up.UG_SetForecolor(color_intensity)

    @staticmethod
    def LCD_SetBackColor(color_intensity:int):
        so_up.UG_SetBackcolor(color_intensity)

    @staticmethod
    def LCD_FillScreen(color_intensity:int):
        """

        """
        so_up.UG_FillScreen(color_intensity)

    @staticmethod
    def LCD_PutString(x: int, y: int, display_string: str):
        """
        x,y(unit:pixel) are the coordinates of where the string that will be displayed

        display_string is  string that will be displayed in the LCD

        """

        # create a c_byte list whose length is the length of the string

        byte = ctypes.c_byte * len(display_string)
        binary = byte()
        for i, char in display_string:
            # dump chars to binary as unicode
            binary[i] = ord(char)
        so_up.UG_PutString(x, y, binary)

    @staticmethod
    def LCD_FillFrame(x1, y1, x2, y2, color_intensity:int):
        so_up.UG_FillFrame(x1, y1, x2, y2, color_intensity)

    @staticmethod
    def LCD_FillRoundFrame(x1, y1, x2, y2, r, color_intensity:int):
        so_up.UG_FillRoundFrame(x1, y1, x2, y2, r, color_intensity)

    @staticmethod
    def LCD_DrawMesh(x1, y1, x2, y2, color_intensity:int):
        so_up.UG_DrawMesh(x1, y1, x2, y2, color_intensity)

    @staticmethod
    def LCD_DrawFrame(x1, y1, x2, y2, color_intensity:int):
        so_up.UG_DrawFrame(x1, y1, x2, y2, color_intensity)

    @staticmethod
    def LCD_DrawRoundFrame(x1, y1, x2, y2, r, color_intensity:int):
        so_up.UG_DrawRoundFrame(x1, y1, x2, y2, r, color_intensity)

    @staticmethod
    def LCD_DrawPixel(x0, y0, color_intensity:int):
        so_up.UG_DrawPixel(x0, y0, color_intensity)

    @staticmethod
    def LCD_DrawCircle(x0, y0, r, color_intensity:int):
        so_up.UG_DrawCircle(x0, y0, r, color_intensity)

    @staticmethod
    def LCD_FillCircle(x0, y0, r, color_intensity:int):
        so_up.UG_FillCircle(x0, y0, r, color_intensity)

    @staticmethod
    def LCD_DrawArc(x0, y0, r, s, color_intensity:int):
        so_up.UG_DrawArc(x0, y0, r, s, color_intensity)

    @staticmethod
    def LCD_DrawLine(x1, y1, x2, y2, color_intensity:int):
        so_up.UG_DrawLine(x1, y1, x2, y2, color_intensity)
        # void UG_DrawArc( UG_S16 x0, UG_S16 y0, UG_S16 r, UG_U8 s, UG_COLOR c );
    # void UG_DrawLine( UG_S16 x1, UG_S16 y1, UG_S16 x2, UG_S16 y2, UG_COLOR c );


if __name__ == "__main__":
    a = UpTech()
    print(so_up)
    pass
