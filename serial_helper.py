import time
from typing import List
import platform
import serial
from serial.tools.list_ports import comports


class SerialHelper:
    """
    所有共享状态变量（如 _serial 和 _is_connected）的访问都添加了对应的锁获取和释放操作。
    移除了 _on_connected_changed 和 _on_data_received 两个线程方法，
    新增了 start_read_thread 线程来不断监听串口设备是否有数据返回。
    新增 DummyLock 类作为在单线程场景下实际使用的锁占位符。
    这是因为如果在单线程的环境中使用普通的锁会降低程序效率，
    而使用 DummyLock 可以不影响程序性能并且可以消除后面调用锁时可能会出现的 NoneType Error 问题。
    另外，在新代码中，我们新增了 start_read_thread 方法和 on_data_received_handler 回调函数，
    可以统一应对串口设备发送过来的数据，并且用户也可以使用 set_on_data_received_handler 方法通过传入回调函数的方式来自定义处理接收到的数据。
    """

    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200, bytesize: int = 8, parity: str = 'N',
                 stopbits: int = 1) -> None:

        self._serial_port: str = port
        self._baudrate: int = baudrate
        self._bytesize: int = bytesize
        self._parity: str = parity
        self._stopbits: int = stopbits

        self._serial_lock = DummyLock()
        self._is_connected_lock = DummyLock()
        self._is_connected: bool = False

    @property
    def is_connected(self) -> bool:
        with self._is_connected_lock:
            return self._is_connected

    @property
    def serial_port(self) -> str:
        return self._serial_port

    @property
    def baudrate(self) -> int:
        return self._baudrate

    @property
    def bytesize(self) -> int:
        return self._bytesize

    @property
    def parity(self) -> str:
        return self._parity

    @property
    def stopbits(self) -> int:
        return self._stopbits

    def connect(self):
        with self._serial_lock:
            if not self.is_connected:
                try:
                    self._serial = serial.Serial(
                        port=self.serial_port,
                        baudrate=self.baudrate,
                        bytesize=self.bytesize,
                        parity=self.parity,
                        stopbits=self.stopbits,
                        timeout=1
                    )
                    with self._is_connected_lock:
                        self._is_connected = True
                    return True
                except serial.serialutil.SerialException as e:
                    print(f"Failed to connect with port {self.serial_port}, baudrate {self.baudrate}: {e}")
        return False

    def disconnect(self):
        with self._serial_lock:
            if self.is_connected and self._serial.isOpen():
                self._serial.close()

    def write(self, data: bytes) -> bool:
        with self._serial_lock:
            try:
                if self.is_connected:
                    self._serial.write(data)
                    return True
            except serial.serialutil.SerialException as e:
                print(f"Serial write error: {e}")
        return False

    def read(self, length: int) -> bytes:
        with self._serial_lock:
            if self.is_connected:
                try:
                    data: bytes = self._serial.read(length)
                    return data
                except serial.serialutil.SerialException as e:
                    print(f"Serial read error: {e}")
        return b''

    def find_usb_tty(self, id_product: int, id_vendor: int) -> List[str]:
        tty_list = []
        if platform.system() == 'Linux':
            for i in comports():
                if 'USB' in i[0] or 'ACM' in i[0]:
                    info = i[2]
                    vendor_id_loc = info.find('idVendor')
                    product_id_loc = info.find('idProduct')
                    if product_id_loc != -1 and vendor_id_loc != -1:
                        vendor_id_str = info[vendor_id_loc:]
                        product_id_str = info[product_id_loc:]
                        vendor_id = int(vendor_id_str.split("=")[1].strip(), 16)
                        product_id = int(product_id_str.split("=")[1].strip(), 16)
                        if product_id == id_product and vendor_id == id_vendor:
                            tty_list.append(i[0])
        return tty_list

    def start_read_thread(self, interval=0.1):
        while True:
            with self._is_connected_lock:
                connected = self.is_connected
            if connected:
                data: bytes = self.read(512)
                if len(data) > 0:
                    self.on_data_received_handler(data)
            time.sleep(interval)

    def set_on_data_received_handler(self, func):
        """set serial data received callback"""
        self.on_data_received_handler = func

    def on_data_received_handler(self, data: bytes):
        """default data received handler if no handler is added"""
        pass


class DummyLock:
    def acquire(self):
        pass

    def release(self):
        pass
