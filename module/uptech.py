import ctypes
import os
from ctypes import cdll, CDLL, Union
import warnings
from ..constant import ENV_LIB_SO_PATH
from .db_tools import persistent_cache

ld_library_path = os.environ.get(ENV_LIB_SO_PATH)


@persistent_cache(f'{ld_library_path}/lb_cache')
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
        warnings.warn('##Uptech: Failed to load libuptech.so##')

    __adc_data_list_type = ctypes.c_uint16 * 10

    __mpu_data_list_type = ctypes.c_float * 3
    _adc_all = __adc_data_list_type()
    _accel_all = __mpu_data_list_type()
    _gyro_all = __mpu_data_list_type()
    _atti_all = __mpu_data_list_type()

    def __init__(self, open_mpu: bool = True,
                 debug: bool = False):
        self.debug = debug

        if open_mpu:
            self.MPU6500_Open()
        if self.debug:
            warnings.warn('Sensor data buffer loaded')

            print(f"Sensor channel Init times: {self.adc_io_open()}")

    @staticmethod
    def adc_io_open():
        """
        open the  adc-io plug
        """
        return UpTech.__lib.adc_io_open()

    @staticmethod
    def adc_io_close():
        """
        close the adc-io plug
        """
        UpTech.__lib.adc_io_close()

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
        UpTech.__lib.ADC_GetAll(UpTech._adc_all)
        return UpTech._adc_all

    @staticmethod
    def set_io_level(index: Union[ctypes.c_uint, int], level: Union[ctypes.c_char, int]):
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
        UpTech.__lib.adc_io_Set(index, level)

    @staticmethod
    def set_all_io_level(level: ctypes.c_uint):
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
        UpTech.__lib.adc_io_SetAll(level)

    @staticmethod
    def get_all_io_mode(buffer: ctypes.c_byte):
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
        return UpTech.__lib.adc_io_ModeGetAll(buffer)

    @staticmethod
    def set_all_io_mode(mode: ctypes.c_int):
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
        UpTech.__lib.adc_io_ModeSetAll(mode)

    @staticmethod
    def set_io_mode(index: ctypes.c_uint, mode: ctypes.c_int):
        """
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
        UpTech.__lib.adc_io_ModeSet(index, mode)

    @staticmethod
    def io_all_channels():
        """
        get all io plug input level

        unsigned 8int
        """

        return tuple(int(x) for x in f'{UpTech.__lib.adc_io_InputGetAll():08b}')

    @staticmethod
    def MPU6500_Open(debug_info: bool = False):
        """
        initialize the MPU6500
        default settings:
            acceleration: -+8G
            gyro: -+2000 degree/s
            sampling rate: 1kHz
        """
        if UpTech.__lib.mpu6500_dmp_init():
            warnings.warn('#failed to initialize MPU6500', category=RuntimeWarning)
        elif debug_info:
            warnings.warn('#MPU6500 successfully initialized')

    @staticmethod
    def acc_all():
        """
        get the acceleration from MPU6500
        """
        UpTech.__lib.mpu6500_Get_Accel(UpTech._accel_all)

        return UpTech._accel_all

    @staticmethod
    def gyro_all():
        """
        get gyro from MPU6500
        """
        UpTech.__lib.mpu6500_Get_Gyro(UpTech._gyro_all)

        return UpTech._gyro_all

    @staticmethod
    def atti_all():
        """
        get attitude from MPU6500
        """

        UpTech.__lib.mpu6500_Get_Attitude(UpTech._atti_all)

        return UpTech._atti_all
