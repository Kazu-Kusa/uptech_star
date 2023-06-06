import threading
from .serial_helper import SerialHelper
from .timer import delay_us


class CloseLoopController:

    def __init__(self, motor_ids_list: tuple = (1, 2, 3, 4), sending_delay: int = 100, debug: bool = False):
        """

        :param motor_ids_list:
        :param sending_delay:
        """
        self._debug = debug
        # 创建串口对象
        self.serial = SerialHelper(con2port_when_created=True, auto_search_port=True)
        self.msg_send_thread = None
        # 发送的数据队列
        self._motor_speed_list: list[int] = [0, 0, 0, 0]
        self._sending_delay = sending_delay
        self._motor_id_list = motor_ids_list
        self.msg_list = []
        self.start_msg_sending()

    @property
    def motor_speed_list(self) -> list[int]:
        return self._motor_speed_list

    @motor_speed_list.setter
    def motor_speed_list(self, new_speed_list: list[int]):
        self._motor_speed_list = new_speed_list

    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, debug: bool):
        self._debug = debug

    @property
    def sending_delay(self) -> int:
        return self._sending_delay

    @sending_delay.setter
    def sending_delay(self, sending_delay: int):
        self._sending_delay = sending_delay

    def start_msg_sending(self):
        # 通信线程创建启动
        self.msg_send_thread = threading.Thread(name="msg_send_thread", target=self.msg_sending_thread)
        self.msg_send_thread.daemon = True
        self.msg_send_thread.start()

    def msg_sending_thread(self):
        """
        串口通信线程发送函数
        :return:
        """
        print(f"msg_sending_thread_start, the debugger is [{self.debug}]")
        while True:
            if self.msg_list:
                temp = self.msg_list.pop(0)
                if self.debug:
                    print(f'\nwriting {temp} to channel,remaining {len(self.msg_list)}')
                self.serial.write(temp)
                delay_us(self.sending_delay)

    @staticmethod
    def makeCmd(cmd: str) -> bytes:
        """
        encode a cmd to a bstring
        :param cmd:
        :return:
        """
        return cmd.encode('ascii') + b'\r'

    @staticmethod
    def makeCmd_list(cmd_list: list[str]) -> bytes:
        """
        encode a list of cmd strings into a single bstring
        :param cmd_list:
        :return:
        """
        temp = b''
        for cmd in cmd_list:
            temp += cmd.encode('ascii') + b'\r'
        return temp

    def open_userInput_channel(self, debug: bool = False) -> None:
        """
        open a user input channel for direct access to the driver
        :return:
        """

        ct = 0
        print('\n\nuser input channel opened\nplease enter cmd below,enter [exit] to end the channel')
        debug_temp = self.debug
        self.debug = debug
        if self.debug:
            self.serial.start_read_thread()

            def handler(data: bytes):
                result = ''
                for i in range(len(data)):
                    try:

                        result += bytes(data[i]).decode('ascii')
                    except UnicodeDecodeError:
                        print('bad char,skip')
                        continue
                print(f'\n>>out[{ct}]: {result}')

            self.serial.set_on_data_received_handler(handler)
        while True:
            user_input = input(f'in[{ct}]: ')
            ct += 1
            # 对输入的内容进行处理
            if user_input == 'exit':
                print('\nuser input channel closed')
                self.debug = debug_temp
                break
            else:
                self.msg_list.append(self.makeCmd(user_input))

    def set_motors_speed(self, speed_list: list[int], id_list: tuple = (1, 2, 3, 4), debug: bool = False):
        if id_list is None:
            id_list = self._motor_id_list
        cmd_list = []
        for i, motor_id in enumerate(id_list):
            cmd_list.append(f'{motor_id}v{speed_list[i]}')
        if debug:
            print(f'- {cmd_list}')
        self.msg_list.append(self.makeCmd_list(cmd_list))
        self.motor_speed_list = speed_list

    def set_all_motors_speed(self, speed: int) -> None:
        self.msg_list.append(self.makeCmd(f'v{speed}'))
        self.motor_speed_list = [speed] * 4

    def set_all_motors_acceleration(self, acceleration: int):
        """
        set the acceleration
        :param acceleration:
        :return:
        """
        assert 0 < acceleration < 30000, "Invalid acceleration value"
        # TODO: all sealed cmd should check if the desired value is valid
        self.msg_list.append(self.makeCmd(f'ac{acceleration}'))
        self.eepSav()

    def eepSav(self):
        """
        save params into to the eeprom,
        all value-setter should call this method to complete the value-setting process
        :return:
        """
        # TODO: pre-complie the 'eepsav' cmd to binary instead of doing complie each time on called
        self.msg_list.append(self.makeCmd('eepsav'))
