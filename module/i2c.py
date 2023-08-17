import sys
from abc import ABCMeta, abstractmethod
from ctypes import c_uint16
from typing import List, Dict, Callable, Optional, Tuple, final

from .onboardsensors import \
    PinSetter, pin_setter_constructor, \
    PinGetter, pin_getter_constructor, \
    PinModeSetter, pin_mode_setter_constructor, \
    HIGH, LOW, OUTPUT, INPUT, multiple_pin_mode_setter_constructor, IndexedGetter, IndexedSetter
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

    def __init__(self, self_address: Optional[int] = None):
        self._target_address: Optional[int] = 0xFF
        self._self_address: Optional[int] = self_address
        self._is_idle: bool = True

        self._received_data_handler: Optional[Callable] = None
        self._sent_data_handler: Optional[Callable] = None
        self._read_buffer = bytearray()
        self._write_buffer = bytearray()

    @abstractmethod
    def begin(self, slave_address: int):
        """
        Initialize I2C communication and set the slave address.

        Args:
            slave_address: The slave address to communicate with.

        Returns:
            None
        """

    @abstractmethod
    def end(self):
        """
        Set SCL low and SDA low.
        End the I2C communication.

        Returns:
            None
        """

    @abstractmethod
    def requestFrom(self, target_address: int, request_data_size: int, stop: bool,
                    register_address: Optional[int] = None):
        """
        Read a specified number of data from the target address.

        Args:
            target_address: The target address to read from.
            request_data_size: The number of data to read.
            stop: Whether to send a stop signal after reading.
            register_address: The register address, optional.

        Returns:
            None
        """

    @final
    def beginTransmission(self, target_address: int):
        """
        Start sending data to the target address.

        Args:
            target_address: The target address to send data to.

        Returns:
            None
        """
        self._target_address = target_address
        self._is_idle = False

    @abstractmethod
    def endTransmission(self, stop: bool):
        """
        End sending data to the target address.

        Args:
            stop: Whether to send a stop signal after sending data.

        Returns:
            None
        """

    @abstractmethod
    def write(self, data):
        """
        Write data to the target address.

        Args:
            data: The data to write.

        Returns:
            None
        """

    @final
    @property
    def available(self) -> int:
        """
        Get the available data in the read buffer.

        Returns:
            The quantity of readable data in the read buffer.
        """
        return self._read_buffer.__len__()

    @final
    def read_byte(self):
        """
        Read a byte of data from the read buffer.

        Returns:
            The read byte of data.
        """
        return self._read_buffer.pop(0)

    @final
    def onReceive(self, handler: Callable):
        """
        Set the callback function for receiving data.

        Args:
            handler: The callback function for receiving data.

        Returns:
            None
        """
        self._received_data_handler = handler

    @final
    def onRequest(self, handler: Callable):
        """
        Set the callback function for requesting data.

        Args:
            handler: The callback function for requesting data.

        Returns:
            None
        """
        self._sent_data_handler = handler


# region CH341
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


# endregion


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
    __speed_delay_table = {
        100: 5,
        400: 2
    }

    @final
    def end(self):
        self.set_ALL_PINS_MODE(OUTPUT)
        self.set_SDA_PIN(LOW)
        self.set_SCL_PIN(LOW)
        self.set_ALL_PINS_MODE(INPUT)

    def write(self, data: bytearray | bytes):
        for byte in data:
            self._write_byte(byte)
            self.delay()

    def requestFrom(self, target_address: int, request_data_size: int, stop: bool, register_address=None):

        self.set_ALL_PINS_MODE(OUTPUT)
        self._write_byte((target_address << 1) + 1)
        self._write_byte(register_address) if register_address else None

        def receive_byte() -> int:
            received_data = 0xFF
            for _ in range(8):
                while not self.get_SCL_PIN():
                    _ += 1
                received_data = (received_data << 1) | self.get_SDA_PIN()
            return received_data

        for _ in range(request_data_size):
            self.set_ALL_PINS_MODE(INPUT)
            self._read_buffer.append(receive_byte())
            self.set_ALL_PINS_MODE(OUTPUT)
            self._ack()

    def _write_byte(self, data):
        if self._is_idle:
            raise ConnectionError('I2C is not transmitting')
        for _ in range(8):
            self.set_SDA_PIN(data & 0x80)
            self.set_SCL_PIN(HIGH)
            self.delay()
            self.set_SCL_PIN(LOW)
            self.set_SDA_PIN(LOW)
            data = data << 1
            self.delay()

    def _start(self):
        self.set_SDA_PIN(HIGH)
        self.set_SCL_PIN(HIGH)
        self.delay()
        self.set_SDA_PIN(LOW)
        self.delay()
        self.set_SCL_PIN(LOW)
        self.delay()

    def _stop(self):
        self.set_SDA_PIN(LOW)
        self.set_SCL_PIN(HIGH)
        self.delay()
        self.set_SDA_PIN(HIGH)

    def _nack(self):
        self.set_SDA_PIN(HIGH)
        self.delay()
        self.set_SCL_PIN(HIGH)
        self.delay()
        self.set_SCL_PIN(LOW)
        self.delay()

    def _ack(self):
        self.set_SDA_PIN(LOW)
        self.delay()
        self.set_SCL_PIN(HIGH)
        self.delay()
        self.set_SCL_PIN(LOW)
        self.delay()
        self.set_SDA_PIN(HIGH)

    def endTransmission(self, stop: bool):
        # TODO : should check if the data in the send buffer are all sent
        self.end() if stop else self._start()

    def begin(self, slave_address: Optional[int] = None):
        """
        init the i2c communication channel, switch two wire
        Returns:

        """
        self._self_address = slave_address
        self.set_ALL_PINS_MODE(OUTPUT)
        self.set_SDA_PIN(HIGH)
        self.set_SCL_PIN(HIGH)
        self.set_ALL_PINS_MODE(INPUT)

    def __init__(self, SDA_PIN: int, SCL_PIN: int,
                 speed: int,
                 indexed_setter: IndexedSetter,
                 indexed_getter: IndexedGetter,
                 indexed_mode_setter: IndexedSetter,
                 self_address: Optional[int] = None):
        if speed not in self.__speed_delay_table:
            raise IndexError(f'speed must in {list(self.__speed_delay_table.keys())}')
        super().__init__(self_address)

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

        self.begin()


def join_bytes_to_uint16(byte_array: bytearray) -> int:
    return int((byte_array[0] << 8) | byte_array[1])


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
