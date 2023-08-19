from abc import ABCMeta, abstractmethod
from typing import Callable, Optional, Tuple, final

from .onboardsensors import \
    PinSetter, pin_setter_constructor, \
    PinGetter, pin_getter_constructor, \
    PinModeSetter, pin_mode_setter_constructor, \
    HIGH, LOW, OUTPUT, INPUT, multiple_pin_mode_setter_constructor, IndexedGetter, IndexedSetter
from .timer import delay_us_constructor


class I2CBase(metaclass=ABCMeta):
    """
    this class is a base class for I2C communication,
    the syntax is similar to the Arduino I2C library
    """

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
    def read_byte(self) -> int:
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
        write_byte = self._write_byte
        set_mode = self.set_ALL_PINS_MODE
        delay = self.delay
        for byte in data:
            set_mode(OUTPUT)
            write_byte(byte)
            set_mode(INPUT)
            delay()

        # TODO should have a ack/nack receiver

    def requestFrom(self, target_address: int, request_data_size: int, stop: bool, register_address=None):

        set_all_pins_mode = self.set_ALL_PINS_MODE
        set_all_pins_mode(OUTPUT)
        ack = self._ack
        buffer_append = self._read_buffer.append
        get_scl_pin = self.get_SCL_PIN
        get_sda_pin = self.get_SDA_PIN
        delay = self.delay
        self._start()
        self._write_byte((target_address << 1) + 1)
        delay()

        def receive_byte() -> int:
            """
            Receive a byte from the slave device.
            Returns: the 8bit byte received from the slave device

            """
            received_data = 0x00
            for _ in range(8):
                while not get_scl_pin():
                    _ += 1
                received_data = (received_data << 1) | get_sda_pin()
            return received_data

        self._write_byte(register_address) if register_address else None
        delay()
        for _ in range(request_data_size):
            set_all_pins_mode(INPUT)
            buffer_append(receive_byte())
            set_all_pins_mode(OUTPUT)
            ack()

        self._stop() if stop else None

    def _write_byte(self, data):
        if self._is_idle:
            raise ConnectionError('I2C is not transmitting')
        set_sda_pin = self.set_SDA_PIN
        set_scl_pin = self.set_SCL_PIN
        delay = self.delay
        for _ in range(8):
            set_sda_pin(data & 0x80)
            set_scl_pin(HIGH)
            delay()
            set_scl_pin(LOW)
            set_sda_pin(LOW)
            data <<= 1
            delay()

    def _start(self):
        delay = self.delay
        self.set_SDA_PIN(HIGH)
        self.set_SCL_PIN(HIGH)
        delay()
        self.set_SDA_PIN(LOW)
        delay()
        self.set_SCL_PIN(LOW)
        delay()

    def _stop(self):
        delay = self.delay
        self.set_SDA_PIN(LOW)
        self.set_SCL_PIN(HIGH)
        delay()
        self.set_SDA_PIN(HIGH)

    def _nack(self):
        delay = self.delay
        self.set_SDA_PIN(HIGH)
        delay()
        self.set_SCL_PIN(HIGH)
        delay()
        self.set_SCL_PIN(LOW)
        delay()

    def _ack(self):
        delay = self.delay
        self.set_SDA_PIN(LOW)
        delay()
        self.set_SCL_PIN(HIGH)
        delay()
        self.set_SCL_PIN(LOW)
        delay()
        self.set_SDA_PIN(HIGH)

    def endTransmission(self, stop: bool):
        # TODO : should check if the data in the send buffer are all sent
        self._stop() if stop else self._start()

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


def join_bytes_to_uint16(byte_high, byte_low) -> int:
    """

    Args:
        byte_high:
        byte_low:

    Returns:

    """
    return int((byte_high << 8) | byte_low)


class SensorI2CExpansion(SimulateI2C):
    """
    this class is specifically for emakefun i2c expansion board.

    only exposed the adc related api

    the expansion board has a default address of 0x24

    the default register address is 0x10
    """

    def __init__(self, expansion_device_addr: int, register_addr: int, SDA_PIN: int, SCL_PIN: int, speed: int,
                 indexed_setter: Callable,
                 indexed_getter: Callable,
                 indexed_mode_setter: Callable):
        """

        Args:
            expansion_device_addr: the address of the expansion board
            register_addr: the address of the register
            SDA_PIN: the pin of the sda pin
            SCL_PIN: the pin of the scl pin
            speed: the speed of the i2c bus
            indexed_setter: the setter that will be called to set the pin level,
            indexed_getter: the getter that will be called to get the pin level,
            indexed_mode_setter: the mode setter that will be called to set the pin mode,input or output
        """
        super().__init__(SDA_PIN=SDA_PIN, SCL_PIN=SCL_PIN, speed=speed,
                         indexed_setter=indexed_setter,
                         indexed_getter=indexed_getter,
                         indexed_mode_setter=indexed_mode_setter)
        self._expansion_device_addr = expansion_device_addr
        self._register_addr = register_addr
        self.begin()

    def get_sensor_adc(self, index: int) -> int:
        """

        Args:
            index: the index of the sensor

        Returns: the adc value of the sensor, resolution is 1024

        """
        self.beginTransmission(self._expansion_device_addr)
        self.requestFrom(self._expansion_device_addr, 2, True, self._register_addr + index * 2)
        self.endTransmission(stop=True)
        return join_bytes_to_uint16(self.read_byte(), self.read_byte())

    def get_all_sensor(self) -> Tuple[int, ...]:
        """

        Returns:

        """
        raise NotImplementedError
