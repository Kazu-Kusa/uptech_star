import sys
from abc import ABCMeta, abstractmethod
from typing import List, Dict
from ctypes import c_uint16
from .serial_helper import SerialHelper, serial_kwargs_factory

"""
CH341可以外接I2C接口的器件，例如常用的24系列串行非易失存储器EEPROM，
支持24C01A，24C02，24C04，24C08，24C16等，以及与之时序兼容的器件，
24系列EEPROM既可以用于配置CH341，也可以用于断电期间保存重要数据。
例如保存产品序列号等识别信息，应用程序可以读出用于识别产品功能等。
如果需要支持24C64、24C256、24C512以及更大容量的EEPROM，请参考CH341评估板资料。

应用程序可以按串口方式读写CH341所连接的24系列EEPROM，方法是：
  设置CH341串口波特率为300，然后以4字节为一组的命令包写串口，
  命令包的首字节必须是@，地址符，对应的十六进制数为40H，
  命令包的第二字节是24系列EEPROM的设备地址，位0是方向标志，0为写，1为读，
  命令包的第三字节是24系列EEPROM的单元地址，
  命令包的第四字节是准备写入24系列EEPROM的一个数据，如果是读操作则指定为00H，
  如果是写操作，那么命令发送成功就说明写成功，对于EEPROM还要延时10mS才能下一个操作，
  如果是读操作，那么命令发送成功后，可以从串口接收到一个字节的数据，就是读出的数据

例如，CH341连接24C0X，A2=A1=A0=GND，将仿真串口的波特率选择为300bps，
可以用串口监控/调试工具软件演示：
1、发出命令包，为4个十六进制数据： 40 A1 01 00
   将24C0X中地址为01H的数据读出，可以从串口接收到一个字节的数据
2、发出命令包，为4个十六进制数据： 40 A0 2A 69
   将一个字节的数据69H写到24C0X中地址为2AH的单元，通常等待10mS后才能进行下一个操作
3、发出命令包，为4个十六进制数据： 40 A5 E7 00
   将24C0X中地址为02E7H的数据读出，可以从串口接收到一个字节的数据
   注意，只有24C08和24C16中有地址为02E7H的数据单元
"""
DEFAULT_I2C_SERIAL_KWARGS = serial_kwargs_factory(baudrate=300)
Hex = int | bytes


class Ch341aApplication(object, metaclass=ABCMeta):
    def __init__(self, port: str, serial_config: Dict):
        self._serial: SerialHelper = SerialHelper(port=port, serial_config=serial_config)

    @abstractmethod
    def read_1char(self, device_addr, register_addr):
        """
        from the i2c serial port read a single char(8bit) of a slave device
        :param device_addr: the device that you want to read
        :param register_addr: the register of the device that you want to read
        :return: 8bit data
        """
        pass

    @abstractmethod
    def write_1char(self, device_addr, register_addr, trunk):
        """
        write a single char(8bit) to a slave device through the i2c serial port
        :param device_addr:  the device that you want to write
        :param register_addr:  the register of the device that you want to write
        :param trunk: the data you want to write
        :return: if the write operation is successful.True for success, False for failure
        """
        pass

    @abstractmethod
    def read(self, size, device_addr, register_addr):
        """
        from the i2c serial port read gavin size data of a slave device,
        :param size: the size of the data,integer only
        :param device_addr: the device that you want to read
        :param register_addr: the register of the device that you want to read
        :return: the data,List of chars(8bit)
        """
        pass

    @abstractmethod
    def write(self, trunk, device_addr, register_addr):
        """
        from the i2c serial port write gavin trunk data to a slave device
        :param trunk:  the data you want to write,List of chars(8bit) or bytearray
        :param device_addr: the device that you want to write
        :param register_addr: the register of the device that you want to write
        :return: if the write operation is successful, True for success, False for failure
        """
        pass

    @property
    def port(self) -> str:
        return self._serial.port

    @port.setter
    def port(self, new_port: str):
        """
        pyserial will reopen the serial port on the serial port change :param value: :return:
        :param new_port:
        :return:
        """
        self._serial.port = new_port


class I2CReader(Ch341aApplication):

    def read_1char(self, device_addr: Hex, register_addr: Hex) -> bytes:
        """
        from the i2c serial port read a single char(8bit) of a slave device
        :param device_addr: the device that you want to read
        :param register_addr: the register of the device that you want to read
        :return: 8bit data
        """
        # send the desired data address to the port
        self._serial.write(f'@{device_addr}{register_addr}'.encode('ascii'))
        return self._serial.read(1)

    def write_1char(self, device_addr: Hex, register_addr: Hex, trunk: bytes) -> bool:
        """
        write a single char(8bit) to a slave device through the i2c serial port
        :param device_addr:  the device that you want to write
        :param register_addr:  the register of the device that you want to write
        :param trunk: the data you want to write
        :return: if the write operation is successful.True for success, False for failure
        """
        return self._serial.write(f'@{device_addr}{register_addr}{trunk}'.encode('ascii'))

    def read(self, size: int, device_addr: Hex, register_addr: Hex) -> List[bytes]:
        """
        from the i2c serial port read gavin size data of a slave device,
        :param size: the size of the data,integer only
        :param device_addr: the device that you want to read
        :param register_addr: the register of the device that you want to read
        :return: the data,List of chars(8bit)
        """
        return ([self.read_1char(device_addr=device_addr,
                                 register_addr=register_addr + i) for i in range(size)])

    def write(self, trunk: List[bytes] | bytearray, device_addr: Hex, register_addr: Hex) -> bool:
        """
        from the i2c serial port write gavin trunk data to a slave device
        :param trunk:  the data you want to write,List of chars(8bit) or bytearray
        :param device_addr: the device that you want to write
        :param register_addr: the register of the device that you want to write
        :return: if the write operation is successful, True for success, False for failure
        """
        return all([self.write_1char(device_addr=device_addr,
                                     register_addr=register_addr + i,
                                     trunk=trunk[i]) for i in range(len(trunk))])


class SensorsExpansion(I2CReader, metaclass=ABCMeta):
    DEVICE_ADDR = 0x24
    ADC_REGISTER = 0x20

    ADC_DATA_TYPE = c_uint16
    ADC_DATA_SIZE = 2
    ADC_CHANNEL_COUNT = 8
    ADC_CHANNEL_ADDR = [ADC_REGISTER + i * ADC_DATA_SIZE for i in range(ADC_CHANNEL_COUNT)]

    def get_adc_data(self, channel: int) -> ADC_DATA_TYPE:
        return c_uint16(int.from_bytes(
            bytes=b''.join(self.read(
                size=self.ADC_DATA_SIZE,
                device_addr=self.DEVICE_ADDR,
                register_addr=self.ADC_CHANNEL_ADDR[channel])),
            byteorder=sys.byteorder))

    def get_all_adc_data(self) -> List[ADC_DATA_TYPE]:
        return [self.get_adc_data(i) for i in range(self.ADC_CHANNEL_COUNT)]
