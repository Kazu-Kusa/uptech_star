import threading
import time

from .serial_helper import SerialHelper


class CloseLoopController:

    def __init__(self):
        # 创建串口对象
        self.ser = SerialHelper()

        self.ser.on_connected_changed(self.myserial_on_connected_changed)

        # 发送的数据队列
        self.msg_list = []
        # 是否连接成功
        self._isConn = True

        # 通信线程创建启动
        sendThread = threading.Thread(name="send_thread", target=self.send_msg)
        sendThread.daemon = False
        sendThread.start()

    # 串口连接状态回调函数
    def myserial_on_connected_changed(self, is_connected: bool):
        if is_connected:
            print("Connected")
            self._isConn = True
            self.ser.connect()
        else:
            print("DisConnected")

    # 串口通信发送
    def write(self, data):
        self.ser.write(data, isHex=True)

    # 串口通信线程发送函数
    def send_msg(self):
        print("send_msg_start")
        while True:
            if len(self.msg_list) > 0 and self._isConn:
                self.ser.write(self.msg_list[0])
                time.sleep(0.0001)
                self.msg_list.remove(self.msg_list[0])

    @staticmethod
    def generateCmd(cmd: str):
        """
        convert a command to a tx/rx binary
        :param cmd: the string that will be converted to binary format according to the convey protocol
        :return: the binary format cmd
        """
        buffer = [0] * (len(cmd) + 1)
        for index, cmd_char in enumerate(cmd):
            buffer[index] = (ord(cmd_char)) & 0xFF
        buffer[len(cmd)] = 0x0D
        return buffer

    def set_motor_speed(self, motor_id: int, speed: int, debug: bool = False):
        """
        控制节点电机运动
        :param motor_id: the id of the motor that you want to control
        :param speed: the desired speed of the motor
        :param debug: if open the debugging info
        :return: None
        """
        cmd = f'{motor_id}v{speed}'  # make the command to string
        data = self.generateCmd(cmd)  # build the command
        self.write(data)  # send the binary data to channel
        if debug:
            print(cmd)


if __name__ == '__main__':
    connect = CloseLoopController()
    time.sleep(1)
    connect.set_motor_speed(4, -9999)
    # connect.set_motor_speed(3, 0)
