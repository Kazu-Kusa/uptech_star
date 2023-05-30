import ctypes
import os
from ctypes import cdll
import warnings
import pigpio

FAN_GPIO_PWM = 18
FAN_pulse_frequency = 20000
FAN_duty_time_us = 1000000
FAN_PWN_range = 100


def load_lib(libname: str) -> object:
    ld_library_path = os.environ.get('LD_LIBRARY_PATH')
    lib_file_name = f'{ld_library_path}/{libname}'
    print(f'Loading [{lib_file_name}]')
    return cdll.LoadLibrary(lib_file_name)


so_up = load_lib('libuptech.so')


class UpTech:
    """
    provides sealed methods accessing to the IOs and builtin sensors
    """
    # TODO: move this type def out of here
    _adc_data_list_type = ctypes.c_uint16 * 10

    __mpu_data_list_type = ctypes.c_float * 3

    def __init__(self, open_mpu: bool = True, debug: bool = False, fan_control: bool = True):
        self.debug = debug

        self._adc_all = self._adc_data_list_type()

        if open_mpu:
            self._accel_all = self.__mpu_data_list_type()
            self._gyro_all = self.__mpu_data_list_type()
            self._atti_all = self.__mpu_data_list_type()
            self.MPU6500_Open()
        if self.debug:
            print('Sensor data buffer loaded')
        if fan_control:
            warnings.warn('loading fan control')
            pigpio.exceptions = True
            self.Pi = pigpio.pi()
            assert self.Pi.connected, 'pi is not connected'
            self.Pi.hardware_PWM(FAN_GPIO_PWM, FAN_pulse_frequency, FAN_duty_time_us)
            self.Pi.set_PWM_range(FAN_GPIO_PWM, FAN_PWN_range)
            warnings.warn('fan control loaded')
        elif debug:
            warnings.warn('fan control disabled')

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

    @property
    def adc_all_channels(self):
        """
        get all adc channels and return they as a tuple
        """
        so_up.ADC_GetAll(self._adc_all)
        return self._adc_all

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
    def get_io(index: int):
        """
        get io plug input level by index
        :param index:
        :return:
        """
        return f'{so_up.adc_io_InputGetAll():08b}'[index]

    @property
    def io_all_channels(self):
        """
        get all io plug input level

        unsigned 8int
        """

        return list([int(x) for x in f'{so_up.adc_io_InputGetAll():08b}'])

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

    @property
    def acc_all(self):
        """
        get the acceleration from MPU6500
        """
        so_up.mpu6500_Get_Accel(self._accel_all)

        return self._accel_all

    @property
    def gyro_all(self):
        """
        get gyro from MPU6500
        """
        so_up.mpu6500_Get_Gyro(self._gyro_all)

        return self._gyro_all

    @property
    def atti_all(self):
        """
        get attitude from MPU6500
        """

        so_up.mpu6500_Get_Attitude(self._atti_all)

        return self._atti_all
