import sys
from abc import ABCMeta, abstractmethod
from ctypes import c_uint16
from typing import List, Dict, Callable, Optional, Tuple

from .onboardsensors import \
    PinSetter, pin_setter_constructor, \
    PinGetter, pin_getter_constructor, \
    PinModeSetter, pin_mode_setter_constructor, \
    HIGH, LOW, OUTPUT, INPUT, multiple_pin_mode_setter_constructor
from .serial_helper import SerialHelper, serial_kwargs_factory
from .timer import delay_us_constructor

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


class I2CBase(metaclass=ABCMeta):

    @abstractmethod
    def begin(self, slave_address: int):
        raise NotImplementedError

    @abstractmethod
    def end(self):
        raise NotImplementedError
    @abstractmethod
    def requestFrom(self, target_address: int, request_data_size: int, stop: bool):
        raise NotImplementedError

    @abstractmethod
    def beginTransmission(self, target_address: int):
        raise NotImplementedError

    @abstractmethod
    def endTransmission(self, stop: bool):
        raise NotImplementedError

    @abstractmethod
    def write(self, data):
        raise NotImplementedError

    @abstractmethod
    def available(self, length: int):
        raise NotImplementedError

    @abstractmethod
    def read_byte(self):
        raise NotImplementedError

    @abstractmethod
    def onReceive(self, handler: Callable):
        raise NotImplementedError

    @abstractmethod
    def onRequest(self, handler: Callable):
        raise NotImplementedError


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


class SensorsSerialExpansion(I2CReader, metaclass=ABCMeta):
    VENDOR_ID = '1a86'
    PRODUCT_ID = '5512'
    DEVICE_ID = f'{VENDOR_ID}:{PRODUCT_ID}'

    DEVICE_ADDR = 0x24
    ADC_REGISTER = 0x20

    ADC_DATA_TYPE = c_uint16
    ADC_DATA_SIZE = 2
    ADC_CHANNEL_COUNT = 8

    ADC_CHANNEL_ADDR = []

    def init_adc_channel_list(self):
        self.ADC_CHANNEL_ADDR = [self.ADC_REGISTER + i * self.ADC_DATA_SIZE for i in range(self.ADC_CHANNEL_COUNT)]

    def get_adc_data(self, channel: int) -> ADC_DATA_TYPE:
        return c_uint16(int.from_bytes(
            bytes=b''.join(self.read(
                size=self.ADC_DATA_SIZE,
                device_addr=self.DEVICE_ADDR,
                register_addr=self.ADC_CHANNEL_ADDR[channel])),
            byteorder=sys.byteorder))

    def get_all_adc_data(self) -> List[ADC_DATA_TYPE]:
        return [self.get_adc_data(i) for i in range(self.ADC_CHANNEL_COUNT)]


class SimulateI2C(I2CBase):
    """
    # 假设要传输的数据为 0b10101010
    data = 0b10101010

    # 从高位开始传输数据
    for i in range(7, -1, -1):
        bit = (data >> i) & 1
        # 在这里执行将 bit 发送到 I2C 总线的操作

    # 从高位开始接收数据
    received_data = 0
    for i in range(7, -1, -1):
        # 在这里执行从 I2C 总线接收一个 bit 的操作，并将其存储在 received_bit 中
        received_bit = 1  # 假设这里的 received_bit 是从 I2C 总线接收到的数据位
        received_data = (received_data << 1) | received_bit

    print(received_data)
    """

    def available(self, length: int):
        pass

    def write(self, data):
        pass

    def onRequest(self, handler: Callable):
        self._sent_data_handler = handler

    def onReceive(self, handler: Callable):
        self._received_data_handler = handler

    def requestFrom(self, target_address: int, request_data_size: int, stop: bool):
        pass

    __speed_delay_table = {
        100: 5,
        400: 2
    }

    # 发送一个字节的数据

    # 读取一个字节的数据
    def _write_byte(self, data):
        for _ in range(8):
            self.set_SDA_PIN(data & 0x80)
            self.get_SCL_PIN(HIGH)
            self.delay()
            self.set_SCL_PIN(LOW)
            self.set_SDA_PIN(LOW)
            data = data << 1
            self.delay()

    def _read_byte(self):
        """
        be sure that the SDA is input output
        Returns: 8-bit data

        """
        received_data = 0x0
        for _ in range(8):
            while not self.get_SCL_PIN():
                pass
            received_data = (received_data << 1) | self.get_SDA_PIN()
        return received_data

    def _nack(self):
        self.set_SDA_PIN(HIGH)  # cpu驱动SDA = 1
        self.delay()
        self.set_SCL_PIN(HIGH)  # 产生一个高电平时钟
        self.delay()
        self.set_SCL_PIN(LOW)
        self.delay()

    def _ack(self):
        self.set_SDA_PIN(LOW)  # cpu驱动SDA = 0
        self.delay()
        self.set_SCL_PIN(HIGH)  # 产生一个高电平时钟
        self.delay()
        self.set_SCL_PIN(LOW)
        self.delay()
        self.set_SDA_PIN(HIGH)  # cpu释放总线

    def read_byte(self):
        raise NotImplementedError

    def endTransmission(self, stop: bool):
        self.set_SDA_PIN(LOW)
        self.set_SCL_PIN(HIGH)
        self.delay()
        self.set_SDA_PIN(HIGH)

    def beginTransmission(self, target_address: int):
        self.set_SDA_PIN(HIGH)  # SDA线高电平，这里就是配置了对应的GPIO管脚输出高电平而已
        self.set_SCL_PIN(HIGH)
        self.delay()  # 需要保证你的SDA线高电平一段时间，如下面SDA = 0，这不延时的话，直接变成0
        self.set_SDA_PIN(LOW)
        self.delay()
        self.set_SCL_PIN(LOW)
        self.delay()

    def begin(self, slave_address: int):
        raise NotImplementedError

    def __init__(self, SDA_PIN: int, SCL_PIN: int, speed: int,
                 indexed_setter: Callable,
                 indexed_getter: Callable,
                 indexed_mode_setter: Callable):
        assert speed in self.__speed_delay_table, "Currently supported speed: [100,400]"
        self._speed = speed
        self._indexed_setter = indexed_setter
        self._indexed_getter = indexed_getter
        self.set_SCL_PIN: PinSetter = pin_setter_constructor(indexed_setter, SCL_PIN)
        self.get_SCL_PIN: PinGetter = pin_getter_constructor(indexed_getter, SCL_PIN)
        self.set_SDA_PIN: PinSetter = pin_setter_constructor(indexed_setter, SDA_PIN)
        self.get_SDA_PIN: PinGetter = pin_getter_constructor(indexed_getter, SDA_PIN)
        self.set_SCL_PIN_MODE: PinModeSetter = pin_mode_setter_constructor(indexed_mode_setter,
                                                                           SCL_PIN)
        self.set_SDA_PIN_MODE: PinModeSetter = pin_mode_setter_constructor(indexed_mode_setter,
                                                                           SDA_PIN)
        self.set_ALL_PINS_MODE: PinModeSetter = multiple_pin_mode_setter_constructor(indexed_mode_setter,
                                                                                     [SDA_PIN, SCL_PIN])
        self.delay = delay_us_constructor(speed)

        self.pin_init()
        self._received_data_handler: Optional[Callable] = None
        self._sent_data_handler: Optional[Callable] = None
        self._read_buffer = bytearray()
        self._write_buffer = bytearray()

    def pin_init(self):
        """
        init the i2c communication channel,switch two wire
        Returns:

        """
        self.set_ALL_PINS_MODE(OUTPUT)
        self.set_SDA_PIN(HIGH)
        self.set_SCL_PIN(HIGH)
        self.set_ALL_PINS_MODE(INPUT)


class SensorI2CExpansion(SimulateI2C):

    def __init__(self, SDA_PIN: int, SCL_PIN: int, speed: int,
                 indexed_setter: Callable,
                 indexed_getter: Callable,
                 indexed_mode_setter: Callable):
        super().__init__(SDA_PIN=SDA_PIN, SCL_PIN=SCL_PIN, speed=speed,
                         indexed_setter=indexed_setter,
                         indexed_getter=indexed_getter,
                         indexed_mode_setter=indexed_mode_setter)

    def get_sensor_adc(self, index: int) -> int:
        raise NotImplementedError

    def get_all_sensor(self) -> Tuple[int, ...]:
        raise NotImplementedError
