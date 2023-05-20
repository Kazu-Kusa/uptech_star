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
        """
        Connect to the serial port with the settings specified in the instance attributes using a thread-safe mechanism.
        Return True if the connection is successful, else False.
        """
        # 使用串口锁 `_serial_lock` 确保线程安全
        with self._serial_lock:
            # 如果当前尚未连接
            if not self.is_connected:
                try:
                    # 创建一个 `Serial` 实例连接到对应的串口，并根据实例属性设置相关参数
                    self._serial = serial.Serial(
                        port=self.serial_port,
                        baudrate=self.baudrate,
                        bytesize=self.bytesize,
                        parity=self.parity,
                        stopbits=self.stopbits,
                        timeout=1
                    )
                    # 设置成功连接标志为 True，使用连接标志锁 `_is_connected_lock` 确保线程安全
                    with self._is_connected_lock:
                        self._is_connected = True
                    # 返回 True 表示连接成功
                    return True
                except serial.serialutil.SerialException as e:
                    # 如果连接失败，则打印错误信息并返回 False 表示连接失败
                    print(f"Failed to connect with port {self.serial_port}, baudrate {self.baudrate}: {e}")
            # 如果已经连接，直接返回 True 表示已连接
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

    def find_usb_tty(self, id_product: int = 0, id_vendor: int = 0) -> List[str]:
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

        # 如果当前操作系统是 Linux，则开始搜索 USB to Serial 设备
        if platform.system() == 'Linux':
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

    def start_read_thread(self, interval=0.1):
        """

        :param interval:
        :return:
        """
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
