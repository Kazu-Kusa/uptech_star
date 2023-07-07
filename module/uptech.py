import ctypes
import os
import threading
from ctypes import cdll
from ctypes import CDLL
import warnings
import pigpio

from ..constant import FAN_GPIO_PWM, FAN_pulse_frequency, FAN_duty_time_us, FAN_PWN_range, ENV_LIB_SO_PATH
from .db_tools import persistent_lru_cache

ld_library_path = os.environ.get(ENV_LIB_SO_PATH)


@persistent_lru_cache(f'{ld_library_path}/lb_cache')
def load_lib(libname: str) -> CDLL:
    lib_file_name = f'{ld_library_path}/{libname}'
    print(f'Loading [{lib_file_name}]')
    return cdll.LoadLibrary(lib_file_name)


class UpTech:
    """
    provides sealed methods accessing to the IOs and builtin sensors
    """
    try:
        __lib = load_lib('libuptech.so')
    except OSError:
        warnings.warn('##Faild to load libuptech.so##')

    __adc_data_list_type = ctypes.c_uint16 * 10

    __mpu_data_list_type = ctypes.c_float * 3

    def __init__(self, open_mpu: bool = True,
                 debug: bool = False,
                 fan_control: bool = True,
                 using_updating_thread: bool = False):
        self.debug = debug

        self._adc_all = self.__adc_data_list_type()
        # 如果没有运行，则启动pigpio守护进程

        self.Pi = pigpio.pi()
        assert self.Pi.connected, 'pi is not connected'
        if open_mpu:
            self._accel_all = self.__mpu_data_list_type()
            self._gyro_all = self.__mpu_data_list_type()
            self._atti_all = self.__mpu_data_list_type()
            self.MPU6500_Open()
        if self.debug:
            print('Sensor data buffer loaded')
        if fan_control:
            warnings.warn('loading fan control')

            self.Pi.hardware_PWM(FAN_GPIO_PWM, FAN_pulse_frequency, FAN_duty_time_us)
            self.Pi.set_PWM_range(FAN_GPIO_PWM, FAN_PWN_range)
            warnings.warn('fan control loaded')
        elif debug:
            warnings.warn('fan control disabled')

        print(f"Sensor channel Init times: {self.ADC_IO_Open()}")

        if using_updating_thread:
            warnings.warn('opening sensors update thread')
            self.io_all_syncing = None
            self.adc_all_syncing = None
            self.open_adc_io_update_thread()
        else:
            warnings.warn('NOT using sensors update thread')

    def FAN_Set_Speed(self, speed: int = 0):
        """
        set the speed of the raspberry's fan

        """
        self.Pi.set_PWM_dutycycle(FAN_GPIO_PWM, speed)

    def ADC_IO_Open(self):
        """
        open the  adc-io plug
        """
        return self.__lib.adc_io_open()

    def ADC_IO_Close(self):
        """
        close the adc-io plug
        """
        self.__lib.adc_io_close()

    @property
    def adc_all_channels(self):
        """
        get all adc channels and return they as a tuple
        """
        self.__lib.ADC_GetAll(self._adc_all)
        return self._adc_all

    def ADC_IO_SetIOLevel(self, index, level):
        self.__lib.adc_io_Set(index, level)

    def ADC_IO_SetAllIOLevel(self, value):
        self.__lib.adc_io_SetAll(value)

    def ADC_IO_SetAllIOMode(self, mode):
        self.__lib.adc_io_ModeSetAll(mode)

    def ADC_IO_SetIOMode(self, index, mode):
        self.__lib.adc_io_ModeSet(index, mode)

    @property
    def io_all_channels(self):
        """
        get all io plug input level

        unsigned 8int
        """

        return list([int(x) for x in f'{self.__lib.adc_io_InputGetAll():08b}'])

    def MPU6500_Open(self, debug_info: bool = False):
        """
        initialize the MPU6500
        default settings:
            acceleration: -+8G
            gyro: -+2000 degree/s
            sampling rate: 1kHz
        """
        if self.__lib.mpu6500_dmp_init():
            warnings.warn('#failed to initialize MPU6500', category=RuntimeWarning)
        elif debug_info:
            warnings.warn('#MPU6500 successfully initialized')

    @property
    def acc_all(self):
        """
        get the acceleration from MPU6500
        """
        self.__lib.mpu6500_Get_Accel(self._accel_all)

        return self._accel_all

    @property
    def gyro_all(self):
        """
        get gyro from MPU6500
        """
        self.__lib.mpu6500_Get_Gyro(self._gyro_all)

        return self._gyro_all

    @property
    def atti_all(self):
        """
        get attitude from MPU6500
        """

        self.__lib.mpu6500_Get_Attitude(self._atti_all)

        return self._atti_all

    def __adc_io_sync_thread(self):
        """
        update data thread
        """
        while 1:
            self.adc_all_syncing = self.adc_all_channels
            self.io_all_syncing = self.io_all_channels

    def open_adc_io_update_thread(self):
        """
        open data update thread
        """
        edge_thread = threading.Thread(name="adc_io_sync_thread", target=self.__adc_io_sync_thread)
        edge_thread.daemon = True
        edge_thread.start()

        if self.debug:
            print('adc-io update thread started')
