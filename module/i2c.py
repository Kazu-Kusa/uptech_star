from abc import ABCMeta, abstractmethod
from typing import Callable, Optional, Tuple, final

from .onboardsensors import \
    PinSetter, pin_setter_constructor, \
    PinGetter, pin_getter_constructor, \
    PinModeSetter, pin_mode_setter_constructor, \
    HIGH, LOW, OUTPUT, INPUT, multiple_pin_mode_setter_constructor, IndexedGetter, IndexedSetter
from .timer import delay_us_constructor


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
