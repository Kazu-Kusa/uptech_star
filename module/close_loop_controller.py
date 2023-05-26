import threading
from .serial_helper import SerialHelper


class CloseLoopController:

    def __init__(self, motor_ids_list: tuple = (1, 2, 3, 4)):
        # 创建串口对象

        self.serial = SerialHelper(con2port_when_created=True, auto_search_port=True)
        self.msg_send_thread = None
        # 发送的数据队列
        self.msg_list = []
        self.start_msg_sending()

        self.motor_id_list = motor_ids_list

    def start_msg_sending(self):
        # 通信线程创建启动
        self.msg_send_thread = threading.Thread(name="msg_send_thread", target=self.msg_sending_thread)
        self.msg_send_thread.daemon = True
        self.msg_send_thread.start()

    def msg_sending_thread(self, print_info: bool = False):
        """
        串口通信线程发送函数
        :return:
        """
        print(f"msg_sending_thread_start, the debugger is [{print_info}]")
        while True:
            if self.msg_list:
                temp = self.msg_list.pop(0)
                if print_info:
                    print(f'writing {temp} to channel,remaining {len(self.msg_list)}')
                self.serial.write(temp)

    @staticmethod
    def generateCmd(cmd: str):
        """
        convert a command to a tx/rx binary
        :param cmd: the string that will be converted to binary format according to the convey protocol
        :return: the binary format cmd
        """
        binary_buffer = [0] * (len(cmd) + 1)
        for index, cmd_char in enumerate(cmd):
            binary_buffer[index] = (ord(cmd_char)) & 0xFF
        binary_buffer[len(cmd)] = 0x0D
        return binary_buffer

    @staticmethod
    def makeCmd(cmd: str) -> bytes:
        return cmd.encode('ascii') + b'\r'

    def set_motors_speed(self, speed_list: list[int], id_list: tuple = (1, 2, 3, 4), debug: bool = False):
        if id_list is None:
            id_list = self.motor_id_list
        cmd_list = []
        for i, motor_id in enumerate(id_list):
            cmd_list.append(self.makeCmd(f'{motor_id}v{speed_list[i]}'))
        if debug:
            print(f'- {cmd_list}')
        self.msg_list += cmd_list

    def set_all_motors_speed(self, speed: int):
        self.msg_list.append(self.makeCmd(f'v{speed}'))

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
        self.serial.write(data)  # send the binary data to channel
        if debug:
            print(cmd)


if __name__ == '__main__':
    connect = CloseLoopController()
