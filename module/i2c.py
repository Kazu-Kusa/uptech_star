from .serial_helper import SerialHelper

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


class I2CReader(object):
    def __init__(self, port: str):
        self._serial: SerialHelper = SerialHelper(port=port)

    @property
    def port(self) -> str:
        return self._serial.port

    @port.setter
    def port(self, new_port: str):
        self._serial.port = new_port

    def read(self, device_addr: int | bytearray | bytes, register_addr: int | bytearray | bytes) -> bytes | bytearray:
        self._serial.write(f'@{device_addr}{register_addr}'.encode('ascii'))
        return self._serial.read(1)

    def write(self, device_addr: int | bytearray | bytes, register_addr: int | bytearray | bytes,
              data: bytes | bytearray) -> bool:
        return self._serial.write(f'@{device_addr}{register_addr}{data}'.encode('ascii'))
