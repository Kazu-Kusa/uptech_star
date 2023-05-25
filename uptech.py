import copy
import ctypes
import sys
import os
from ctypes import cdll
import warnings
import pigpio

FAN_GPIO_PWM = 18
FAN_pulse_frequency = 20000
FAN_duty_time_us = 1000000
FAN_PWN_range = 100

ld_library_path = os.environ.get('LD_LIBRARY_PATH')
lib_file_name = f'{ld_library_path}/libuptech.so'
print(f'Loading [{lib_file_name}]')
so_up = cdll.LoadLibrary(lib_file_name)


class UpTech:
    """
    provides sealed methods accessing to the IOs and builtin sensors
    """

    # region font size definitions
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
    # endregion

    # region color Hex value
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
    # endregion

    __adc_data = ctypes.c_uint16 * 10

    __mpu_float = ctypes.c_float * 3

    def __init__(self, open_mpu: bool = True, debug=False):
        self.debug = debug
        pigpio.exceptions = True
        self.Pi = pigpio.pi()
        assert self.Pi.connected, 'pi is not connected'

        self.adc_all = self.__adc_data()
        self.io_all = []

        if open_mpu:
            self.accel_all = self.__mpu_float()
            self.gyro_all = self.__mpu_float()
            self.atti_all = self.__mpu_float()
            self.MPU6500_Open()
        if self.debug:
            print('Sensor data temp loaded')

        self.Pi.hardware_PWM(FAN_GPIO_PWM, FAN_pulse_frequency, FAN_duty_time_us)
        self.Pi.set_PWM_range(FAN_GPIO_PWM, FAN_PWN_range)

    def FAN_Set_Speed(self, speed: int = 0):
        """
        set the speed of the raspberry's fan

        """
        self.Pi.set_PWM_dutycycle(FAN_GPIO_PWM, speed)

    @staticmethod
    def ADC_IO_Open():
        """
        open the  adc-io plug
        """
        return so_up.adc_io_open()

    @staticmethod
    def ADC_IO_Close():
        """
        close the adc-io plug
        """
        so_up.adc_io_close()

    def ADC_Get_All_Channel(self):
        """
        get all adc channels and return they as a tuple
        """
        so_up.ADC_GetAll(self.adc_all)
        return self.adc_all

    @staticmethod
    def ADC_Led_SetColor(index: int, color: int):
        """
        set the color of the LED according to index and color
        """
        so_up.adc_led_set(index, color)

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
    def MPU6500_Open(debug_info: bool = False):
        """
        initialize the MPU6500
        default settings:
            acceleration: -+8G
            gyro: -+2000 degree/s
            sampling rate: 1kHz
        """
        if so_up.mpu6500_dmp_init():
            warnings.warn('#failed to initialize MPU6500', category=RuntimeWarning)
        elif debug_info:
            warnings.warn('#MPU6500 successfully initialized')

    def MPU6500_GetAccel(self):
        """
        get the acceleration from MPU6500
        """
        so_up.mpu6500_Get_Accel(self.accel_all)

        return self.accel_all

    def MPU6500_GetGyro(self):
        """
        get gyro from MPU6500
        """
        so_up.mpu6500_Get_Gyro(self.gyro_all)

        return self.gyro_all

    def MPU6500_GetAttitude(self):
        """
        get attitude from MPU6500
        """

        so_up.mpu6500_Get_Attitude(self.atti_all)

        return self.atti_all

    @staticmethod
    def LCD_Open(direction: int = 2):
        """
        open with lcd ,and set the LCD displaying direction

        1 for vertical, 2 for horizontal
        """
        assert direction == 1 or direction == 2, "1 for vertical and 2 for horizontal"

        return so_up.lcd_open(direction)

    @staticmethod
    def LCD_Refresh():
        """
        clear the displayed contents
        """
        so_up.LCD_Refresh()

    @staticmethod
    def LCD_SetFontSize(font_size: int):

        so_up.LCD_SetFont(font_size)

    @staticmethod
    def LCD_SetForeColor(color: int):
        """
        set the fore color
        """
        so_up.UG_SetForecolor(color)

    @staticmethod
    def LCD_SetBackColor(color: int):
        """
        set the LCD background color
        """
        so_up.UG_SetBackcolor(color)

    @staticmethod
    def LCD_FillScreen(color: int):
        """
        fill the screen with the given color
        """
        so_up.UG_FillScreen(color)

    @staticmethod
    def LCD_PutString(x: int, y: int, display_string: str):
        """
        x,y(unit:pixel) are the coordinates of where the string that will be displayed

        display_string is  string that will be displayed in the LCD

        """

        # create a c_byte list whose length is the length of the string

        byte = ctypes.c_byte * len(display_string)
        binary = byte()
        for i, char in enumerate(display_string):
            # dump chars to binary as unicode
            binary[i] = ord(char)
        so_up.UG_PutString(x, y, binary)

    @staticmethod
    def LCD_FillFrame(x1, y1, x2, y2, color: int):
        so_up.UG_FillFrame(x1, y1, x2, y2, color)

    @staticmethod
    def LCD_FillRoundFrame(x1, y1, x2, y2, r, color: int):
        so_up.UG_FillRoundFrame(x1, y1, x2, y2, r, color)

    @staticmethod
    def LCD_DrawMesh(x1, y1, x2, y2, color: int):
        so_up.UG_DrawMesh(x1, y1, x2, y2, color)

    @staticmethod
    def LCD_DrawFrame(x1, y1, x2, y2, color: int):
        so_up.UG_DrawFrame(x1, y1, x2, y2, color)

    @staticmethod
    def LCD_DrawRoundFrame(x1, y1, x2, y2, r, color: int):
        so_up.UG_DrawRoundFrame(x1, y1, x2, y2, r, color)

    @staticmethod
    def LCD_DrawPixel(x0, y0, color: int):
        so_up.UG_DrawPixel(x0, y0, color)

    @staticmethod
    def LCD_DrawCircle(x0, y0, r, color: int):
        so_up.UG_DrawCircle(x0, y0, r, color)

    @staticmethod
    def LCD_FillCircle(x0, y0, r, color: int):
        so_up.UG_FillCircle(x0, y0, r, color)

    @staticmethod
    def LCD_DrawArc(x0, y0, r, s, color: int):
        so_up.UG_DrawArc(x0, y0, r, s, color)

    @staticmethod
    def LCD_DrawLine(x1, y1, x2, y2, color: int):
        so_up.UG_DrawLine(x1, y1, x2, y2, color)


if __name__ == "__main__":
    a = UpTech()

    pass
