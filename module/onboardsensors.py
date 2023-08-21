import ctypes
import warnings
from time import perf_counter_ns
from typing import Callable, Sequence

from .os_tools import load_lib
from ..constant import MIN_SAMPLE_INTERVAL_MS

PinModeSetter = Callable[[int], None]
PinSetter = Callable[[int], None]
PinGetter = Callable[[], int]

IndexedGetter = Callable[[int], int]
IndexedSetter = Callable[[int, int], None]

OUTPUT = 1
INPUT = 0
HIGH = 1
LOW = 0


class OnBoardSensors:
    """
    provides sealed methods accessing to the IOs and builtin sensors
    """
    try:
        __lib = load_lib('libuptech.so')
    except OSError:
        warnings.warn('##Uptech: Failed to load libuptech.so##')

    __adc_data_list_type = ctypes.c_uint16 * 10

    __mpu_data_list_type = ctypes.c_float * 3
    _adc_all = __adc_data_list_type()
    _accel_all = __mpu_data_list_type()
    _gyro_all = __mpu_data_list_type()
    _atti_all = __mpu_data_list_type()
    last_update_timestamp = perf_counter_ns()
    min_sample_interval = MIN_SAMPLE_INTERVAL_MS * 1000000

    def __init__(self, open_mpu: bool = True,
                 debug: bool = False):
        self.debug = debug

        self.MPU6500_Open() if open_mpu else None
        success = self.adc_io_open()
        print(f"Sensor channel Init times: {success}") if self.debug else None

    @staticmethod
    def adc_io_open():
        """
        open the adc-io plug
        """
        return OnBoardSensors.__lib.adc_io_open()

    @staticmethod
    def adc_io_close():
        """
        close the adc-io plug
        """
        OnBoardSensors.__lib.adc_io_close()

    @staticmethod
    def adc_all_channels():
        """
        这个函数的功能是从ADC（模拟到数字转换器）获取多个值，
        并将这些值存储到指定的内存位置。它通过spi_xfer函数调用来与ADC进行通信，并将获取的结果转换为16位整数，
        并存储到指定内存位置。函数的返回值为0表示操作成功，-1表示操作失败。

        int __fastcall ADC_GetAll(int a1)
        {
          char *v2;        // 声明一个指向字符的指针v2
          int v3;          // 声明一个整型变量v3
          __int16 v4;      // 声明一个16位整型变量v4
          __int16 v5;      // 声明一个16位整型变量v5
          char v7;         // 声明一个字符变量v7，该变量会被按引用传递

          if (pi_1 < 0)    // 检查一个全局变量pi_1是否小于0，如果是，则返回-1
            return -1;

          spi_xfer(pi_1);  // 调用spi_xfer函数，传递pi_1作为参数

          v2 = &v7;        // 将v2指向变量v7的地址
          v3 = a1 - 2;     // 将v3设置为a1减去2，表示指定内存位置的偏移量

          do
          {
            v4 = (unsigned __int8)v2[2];        // 将v2[2]转换为8位无符号整型并赋值给v4
            v5 = (unsigned __int8)v2[1];        // 将v2[1]转换为8位无符号整型并赋值给v5
            v2 += 2;                            // 增加v2的偏移量
            *(_WORD *)(v3 + 2) = v5 | (v4 << 8); // 将v5和v4的组合结果存储到指定内存位置
            v3 += 2;                            // 增加v3的偏移量
          }
          while (a1 + 18 != v3);                 // 当a1和v3的和不等于18时循环

          return 0;                             // 返回0表示操作成功
        }
        """
        current = perf_counter_ns()
        if current - OnBoardSensors.last_update_timestamp < OnBoardSensors.min_sample_interval:
            OnBoardSensors.last_update_timestamp = current
            return OnBoardSensors.acc_all
        OnBoardSensors.__lib.ADC_GetAll(OnBoardSensors._adc_all)
        return OnBoardSensors._adc_all

    @staticmethod
    def set_io_level(index: int, level: int):
        """
        int __fastcall adc_io_Set(unsigned int a1, char a2)
        {
          char v3[12]; // [sp+4h] [bp-Ch] BYREF

          if ( a1 > 7 )
            return -1;
          v3[0] = a1 + 24;
          v3[1] = a2;
          if ( pi_1 < 0 )
            return -1;
          spi_write(pi_1, hspi1, v3, 2);
          return 0;
        }
        """
        OnBoardSensors.__lib.adc_io_Set(index, level)

    @staticmethod
    def set_all_io_level(level: int):
        """
        int __fastcall adc_io_SetAll(unsigned int a1)
        {
          char *v1; // r3
          char v3[8]; // [sp+4h] [bp-14h] BYREF
          char v4; // [sp+Ch] [bp-Ch] BYREF

          v1 = v3;
          do
          {
            *++v1 = (a1 & 1) != 0;
            a1 >>= 1;
          }
          while ( &v4 != v1 );
          v3[0] = 24;
          if ( pi_1 < 0 )
            return -1;
          spi_write(pi_1, hspi1, v3, 9);
          return 0;
        }
        """
        OnBoardSensors.__lib.adc_io_SetAll(level)

    @staticmethod
    def get_all_io_mode(buffer: int):
        """
        int __fastcall adc_io_ModeGetAll(_BYTE *a1)
        {
          int result; // r0
          char v3; // [sp+Dh] [bp-Bh]

          if ( pi_1 < 0 )
            return -1;
          spi_xfer(pi_1);
          result = 0;
          *a1 = v3;
          return result;
        }
        """
        return OnBoardSensors.__lib.adc_io_ModeGetAll(buffer)

    @staticmethod
    def get_io_level(index: int) -> int:

        return (OnBoardSensors.__lib.adc_io_InputGetAll() >> index) & 1

    @staticmethod
    def set_all_io_mode(mode: int):
        """
        int __fastcall adc_io_ModeSetAll(char a1)
        {
          char v2[12]; // [sp+4h] [bp-Ch] BYREF

          v2[1] = a1;
          v2[0] = 21;
          if ( pi_1 < 0 )
            return -1;
          spi_write(pi_1, hspi1, v2, 2);
          return 0;
        }
        """
        OnBoardSensors.__lib.adc_io_ModeSetAll(mode)

    @staticmethod
    def set_io_mode(index: int, mode: int):
        """
        change the mode of the adc-io plug at index,mode 1 for output, 0 for input

        int __fastcall adc_io_ModeSet(unsigned int a1, int a2)
        {
          char v2; // r4
          char v4[9]; // [sp+7h] [bp-9h] BYREF

          if ( a1 > 7 )
            return -1;
          v2 = a1;
          if ( a2 )
          {
            if ( !j_adc_io_ModeGetAll(v4) )
            {
              v4[0] |= 1 << v2;
              return j_adc_io_ModeSetAll();
            }
            return -1;
          }
          if ( j_adc_io_ModeGetAll(v4) )
            return -1;
          v4[0] &= ~(1 << v2);
          return j_adc_io_ModeSetAll();
        }
        """
        OnBoardSensors.__lib.adc_io_ModeSet(index, mode)

    @staticmethod
    def io_all_channels():
        """
        get all io plug input level

        unsigned 8int
        """

        return tuple((OnBoardSensors.__lib.adc_io_InputGetAll() >> i) & 1 for i in range(7, -1, -1))

    @staticmethod
    def MPU6500_Open(debug_info: bool = False):
        """
        initialize the MPU6500
        default settings:
            acceleration: -+8G
            gyro: -+2000 degree/s
            sampling rate: 1kHz
        """
        if OnBoardSensors.__lib.mpu6500_dmp_init():
            warnings.warn('#failed to initialize MPU6500')
        elif debug_info:
            warnings.warn('#MPU6500 successfully initialized')

    @staticmethod
    def acc_all():
        """
        get the acceleration from MPU6500
        """
        OnBoardSensors.__lib.mpu6500_Get_Accel(OnBoardSensors._accel_all)

        return OnBoardSensors._accel_all

    @staticmethod
    def gyro_all():
        """
        get gyro from MPU6500
        """
        OnBoardSensors.__lib.mpu6500_Get_Gyro(OnBoardSensors._gyro_all)

        return OnBoardSensors._gyro_all

    @staticmethod
    def atti_all():
        """
        Get attitude from MPU6500

        NOTE:
            the sampling frequency of the attitude data updates every 10ms.
            So, high sampling-frequency may not be a good option
        """

        OnBoardSensors.__lib.mpu6500_Get_Attitude(OnBoardSensors._atti_all)

        return OnBoardSensors._atti_all

    @staticmethod
    def get_handle(attr_name: str):
        return getattr(OnBoardSensors.__lib, attr_name)


def pin_setter_constructor(indexed_setter: IndexedSetter, pin: int) -> PinSetter:
    """

    Args:
        indexed_setter: the function that
        pin: the pin to be connected

    Returns:

    """

    def set_pin_level(level: int):
        indexed_setter(pin, level)

    return set_pin_level


def pin_getter_constructor(indexed_getter: IndexedGetter, pin: int) -> PinGetter:
    """

    Args:
        indexed_getter:
        pin:

    Returns:

    """

    def get_pin_level() -> int:
        return indexed_getter(pin)

    return get_pin_level


def pin_mode_setter_constructor(indexed_mode_setter: IndexedSetter, pin: int) -> PinModeSetter:
    """

    Args:
        indexed_mode_setter: the function that sets the pin mode
        pin: the pin to be connected

    Returns:
        the function that sets the pin mode with built-in pin value

    """

    def set_pin_mode(mode: int):
        indexed_mode_setter(pin, mode)

    return set_pin_mode


def multiple_pin_mode_setter_constructor(indexed_mode_setter: IndexedSetter, pins: Sequence[int]) -> PinModeSetter:
    """

    Args:
        pins: the pin to be connected
        indexed_mode_setter: the function that sets the pin mode


    Returns:
        the function that sets the pin mode with built-in pin value

    """

    def set_pin_mode(mode: int):
        for pin in pins:
            indexed_mode_setter(pin, mode)

    return set_pin_mode
