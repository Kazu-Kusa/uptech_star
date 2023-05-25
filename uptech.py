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
    # TODO: move this type def out of here
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

    def get_io(self, index: int):

        # 计算要移动的位数
        shift = index * 8
        # 移动到最低 8 位，并获取末尾 8 位的值
        byte_value = (self.ADC_IO_GetAllInputLevel() >> shift) & 0xff
        return byte_value

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

        unsigned 8int
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


if __name__ == "__main__":
    a = UpTech()

    pass
