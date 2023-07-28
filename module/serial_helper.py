from time import sleep
from typing import List, Callable, Any, Optional, ByteString, Union, Dict
from types import MappingProxyType
import serial
from serial import Serial, EIGHTBITS, PARITY_NONE, STOPBITS_ONE
from serial.tools.list_ports import comports
from serial.threaded import ReaderThread, Protocol
from serial.serialutil import SerialException
import warnings

ReadHandler = Callable[[bytes | bytearray], Optional[Any]]
DEFAULT_SERIAL_KWARGS = MappingProxyType({'baudrate': 115200,
                                          'bytesize': EIGHTBITS,
                                          'parity': PARITY_NONE,
                                          'stopbits': STOPBITS_ONE,
                                          'timeout': 2})


def serial_kwargs_factory(baudrate: int = 115200,
                          bytesize: int = EIGHTBITS,
                          parity: str = PARITY_NONE,
                          stopbits: int = STOPBITS_ONE,
                          timeout: float = 2) -> MappingProxyType:
    return MappingProxyType({'baudrate': baudrate,
                             'bytesize': bytesize,
                             'parity': parity,
                             'stopbits': stopbits,
                             'timeout': timeout})


CODING_METHOD = 'ascii'


def default_read_handler(data: bytes | bytearray) -> None:
    print(f'\n##Received:{data.decode(CODING_METHOD)}')


class ReadProtocol(Protocol):

    def __init__(self, read_handler: Optional[ReadHandler] = None):
        self._read_handler: ReadHandler = read_handler if read_handler else lambda data: None

    def connection_made(self, transport):
        """Called when reader thread is started"""
        warnings.warn('##ReadProtocol has been Set##')

    def data_received(self, data):
        """Called with snippets received from the serial port"""
        self._read_handler(data)


def new_ReadProtocol_factory(read_handler: Optional[ReadHandler] = None) -> Callable[[], ReadProtocol]:
    def factory():
        return ReadProtocol(read_handler)

    return factory


class SerialHelper:

    def __init__(self, port: Optional[str] = None, serial_config: Optional[dict] = DEFAULT_SERIAL_KWARGS):
        """
        :param serial_config: a dict that contains the critical transport parameters
        :param port: the serial port to use
        """
        available_serial_ports = find_serial_ports()
        assert available_serial_ports, "No serial ports FOUND!"
        self._serial: Serial = Serial(port=port, **serial_config)
        if port is None:

            # try to search for a new port
            warnings.warn('Searching available Ports')
            print(f'Available ports: {available_serial_ports}')
            for i in available_serial_ports:
                self._serial.port = i
                print(f'try to open to {self._serial.port}')
                if self.open():
                    break

        self._read_thread: Optional[ReaderThread] = None

    @property
    def is_connected(self) -> bool:

        return self._serial.isOpen()

    @property
    def port(self) -> str:
        return self._serial.port

    @port.setter
    def port(self, value: str):
        """
        pyserial will reopen the serial port on the serial port change
        :param value:
        :return:
        """
        self._serial.port = value

    def open(self, logging: bool = True) -> bool:
        """
        Connect to the serial port with the settings specified in the instance attributes using a thread-safe mechanism.
        Return True if the connection is successful, else False.
        """
        # 如果当前尚未连接
        try:
            # 创建一个 `Serial` 实例连接到对应的串口，并根据实例属性设置相关参数
            self._serial.open() if not self._serial.isOpen() else None
            print(f"##INFO:: Successfully open [{self._serial.port}]##") if logging else None
            # 如果已经连接，直接返回 True 表示已连接
            return True
        except SerialException:
            print(f'##INFO:: Failed to open [{self._serial.port}]##') if not self._serial.isOpen() and logging else None
            return False

    def close(self):
        """
        disconnects the connection
        :return:
        """
        self._serial.close()

    def write(self, data: ByteString) -> bool:
        """
        向串口设备中写入二进制数据。

        Args:
            data: 要写入的二进制数据

        Returns:
            如果写入成功则返回 True，否则返回 False。

        Raises:
            无异常抛出。

        Examples:
            serial = SerialHelper()
            if serial.write(b'hello world'):
                print('Data was successfully written to serial port.')
            else:
                print('Failed to write data to serial port.')

        Note:
            1. 此方法需要确保串口设备已经连接并打开，并且调用此方法前应该先检查设备的状态是否正常。
            2. 在多线程或多进程环境下使用此方法时，需要确保对串口上下文对象（即 SerialPort 类的实例）进行正确的锁定保护，以避免多个线程或进程同时访问串口设备造成不可预期的错误。
        """
        try:
            self._serial.write(data)
            return True
        except SerialException:
            warnings.warn("#Exception:: Serial write error")
            return False

    def read(self, length: int) -> bytes | bytearray:
        """
        从串口设备中读取指定长度的字节数据。

        Args:
            length: 整数类型，要读取的字节长度。

        Returns:
            字节串类型，表示所读取的字节数据。如果读取失败，则返回一个空字节串（b''）。

        Raises:
            无异常抛出。

        Example:
            data = serial.read(length=10)
            print(data)

        Note:
            如果连接断开或者读取过程中发生异常，会在控制台打印错误信息并返回一个空字节串（b''）。
        """
        try:
            return self._serial.read(length)
        except SerialException:
            warnings.warn("Exception:: Serial read error")
        return b''

    def start_read_thread(self, read_handler: [ReadHandler]) -> None:
        """
        Start the thread reading loop.
        :return:
        """
        warnings.warn('##Start Read Thread##')
        self._read_thread = ReaderThread(serial_instance=self._serial,
                                         protocol_factory=new_ReadProtocol_factory(read_handler))
        self._read_thread.daemon = True
        self._read_thread.start()

    def stop_read_thread(self) -> None:
        self._read_thread.stop()


def find_usb_tty(id_product: int = 0, id_vendor: int = 0) -> List[str]:
    """
    该函数实现在 Linux 系统下查找指定厂商和产品 ID 的 USB 串口设备，并返回设备名列表。

    具体实现方式是通过调用 serial.tools.list_ports.comports() 函数获取当前系统可用的串口设备信息，
    检查每个设备名称中是否包含 "USB" 或者 "ACM" 关键字（因为基本上所有的 USB 转串口设备都会以这些字符开头），
    然后进一步解析设备的 USB 相关属性信息来确定其所属厂商和产品类型。

    此处使用了 Python 库 serial 提供的 list_ports.comports() 函数，
    它的功能是获取当前系统的可用串口设备列表。调用该函数时，操作系统将扫描所有可能的串口设备号，
    并尝试打开其中可用的端口，提取并返回它们的相关信息，包括设备名、描述信息、VID/PID 等。

    Args:
    id_vendor: 符合条件的 USB 设备的厂商 ID（默认为 0）
    id_product: 符合条件的 USB 设备的产品 ID（默认为 0）

    Returns:
    一个字符串列表，包含所有符合条件的 USB to Serial 转换器设备名（如 '/dev/ttyUSB0'）

    Examples:
    usb = USBFinder()
    tty_list = usb.find_usb_tty(id_vendor=1027, id_product=24577)
    print(tty_list)

    >> ['/dev/ttyUSB0', '/dev/ttyUSB1']

    Note:
    需要先安装 pyserial 模块，并且当前用户需要有足够权限访问串口设备。


    """
    # 初始化结果列表
    tty_list = []

    # 查询系统中所有可用串口
    for i in comports():
        # 判断串口文件名是否包含有 "USB" 或 "ACM"
        if 'USB' in i[0] or 'ACM' in i[0]:
            # 读取串口设备的描述符信息（字符串格式）
            info = i[2]
            # 查找设备描述符中的 idVendor 和 idProduct 字段
            vendor_id_loc = info.find('idVendor')
            product_id_loc = info.find('idProduct')
            # 如果设备描述符中存在产品 ID 和厂商 ID，则尝试解析出这两个值并进行匹配
            if product_id_loc != -1 and vendor_id_loc != -1:
                vendor_id_str = info[vendor_id_loc:]
                product_id_str = info[product_id_loc:]
                vendor_id = int(vendor_id_str.split("=")[1].strip(), 16)
                product_id = int(product_id_str.split("=")[1].strip(), 16)
                if product_id == id_product and vendor_id == id_vendor:
                    tty_list.append(i[0])  # 将符合条件的串口设备加入到结果列表中

    # 返回结果列表
    return tty_list


def find_serial_ports() -> List[str]:
    return [port.device for port in serial.tools.list_ports.comports()]
