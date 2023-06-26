import os
import threading
import time
from typing import List, Tuple, Optional, Union
from .serial_helper import SerialHelper
from .timer import delay_us
from .db_tools import persistent_lru_cache
from .constant import ENV_CACHE_DIR_PATH

cache_dir = os.environ.get(ENV_CACHE_DIR_PATH)


class CloseLoopController:

    def __init__(self, motor_ids_list: Tuple[int, int, int, int], sending_delay: int = 100, debug: bool = False):
        """

        :param motor_ids_list: the id of the motor,represent as follows [fl,rl,rr,fr]
        :param sending_delay:
        """
        self._debug = debug
        # 创建串口对象
        self.serial = SerialHelper(con2port_when_created=True, auto_search_port=True)
        self.msg_send_thread = None
        # 发送的数据队列
        self._motor_speed_list: Tuple[int, int, int, int] = (0, 0, 0, 0)
        self._sending_delay: int = sending_delay
        self._motor_id_list: Tuple[int, int, int, int] = motor_ids_list
        self.msg_list = [self.makeCmd('RESET')]

        self.start_msg_sending()

    @property
    def motor_id_list(self) -> Tuple[int, int, int, int]:
        return self._motor_id_list

    @property
    def motor_speed_list(self) -> Tuple[int, int, int, int]:
        return self._motor_speed_list

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

    def start_msg_sending(self) -> None:
        # 通信线程创建启动
        self.msg_send_thread = threading.Thread(name="msg_send_thread", target=self.msg_sending_thread)
        self.msg_send_thread.daemon = True
        self.msg_send_thread.start()

    def msg_sending_thread(self) -> None:
        """
        串口通信线程发送函数
        :return:
        """
        print(f"msg_sending_thread_start, the debugger is [{self.debug}]")

        def sending_loop() -> None:
            while True:
                if self.msg_list:
                    self.serial.write(self.msg_list.pop(0))
                    delay_us(self.sending_delay)

        def sending_loop_debugging() -> None:
            while True:
                if self.msg_list:
                    temp = self.msg_list.pop(0)
                    print(f'\nwriting {temp} to channel,remaining {len(self.msg_list)}')
                    self.serial.write(temp)
                    delay_us(self.sending_delay)

        if self.debug:
            sending_loop_debugging()
        else:
            sending_loop()

    def move_cmd(self, left_speed: int, right_speed: int) -> None:
        """
        control the motor
        :param left_speed:
        :param right_speed:
        :return:
        """
        self.set_motors_speed((left_speed, left_speed, right_speed, right_speed))

    @staticmethod
    def makeCmd(cmd: str) -> bytes:
        """
        encode a cmd to a bstring
        :param cmd:
        :return:
        """
        return cmd.encode('ascii') + b'\r'

    @staticmethod
    def makeCmd_list(cmd_list: List[str]) -> bytes:
        """
        encode a list of cmd strings into a single bstring
        :param cmd_list:
        :return:
        """
        return b'\r'.join(cmd.encode('ascii') for cmd in cmd_list)

    @staticmethod
    def is_list_all_zero(lst: Union[List[int], Tuple[int, ...]]) -> bool:
        return all(element == 0 for element in lst)

    def set_motors_speed(self, speed_list: Tuple[int, int, int, int],
                         direction_list: Tuple[int, int, int, int] = (1, 1, 1, 1)) -> None:
        if self.is_list_all_zero(speed_list):
            self.set_all_motors_speed(0)
        else:
            cmd_list = []
            for i, (motor_id, speed, direction) in enumerate(zip(self._motor_id_list, speed_list, direction_list)):
                if speed == self._motor_speed_list[i]:
                    continue
                cmd_list.append(f'{motor_id}v{speed * direction}')

            if cmd_list:
                self.msg_list.append(self.makeCmd_list(cmd_list))
        self._motor_speed_list = speed_list

    def set_all_motors_speed(self, speed: int) -> None:
        # TODO: should check before setting
        self.msg_list.append(self.makeCmd(f'v{speed}'))
        self._motor_speed_list = [speed] * 4

    def set_all_motors_acceleration(self, acceleration: int) -> None:
        """
        set the acceleration
        :param acceleration:
        :return:
        """
        assert 0 < acceleration < 30000, "Invalid acceleration value"
        # TODO: all sealed cmd should check if the desired value is valid
        self.msg_list.append(self.makeCmd(f'ac{acceleration}'))
        self.eepSav()

    def eepSav(self) -> None:
        """
        save params into to the eeprom,
        all value-setter should call this method to complete the value-setting process
        :return:
        """
        # TODO: pre-compile the 'eepsav' cmd to binary instead of doing compile each time on called
        self.msg_list.append(self.makeCmd('eepsav'))

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


def motor_speed_test(speed_level: int = 11, interval: float = 1, using_id: bool = True, laps: int = 3) -> None:
    """
    motor speed test function,used to test and check  if the driver configurations are correct
    :param speed_level:
    :param interval:
    :param using_id:
    :param laps:
    :return:
    """
    con = CloseLoopController(motor_ids_list=(4, 3, 1, 2))
    try:
        for _ in range(laps):
            if using_id:
                for i in range(speed_level):
                    print(f'doing {i * 1000}')
                    con.set_motors_speed([i * 1000] * 4)
                    time.sleep(interval)
            else:
                for i in range(speed_level):
                    print(f'doing {i * 1000}')
                    con.set_all_motors_speed(i * 1000)
                    time.sleep(interval)
    finally:
        con.set_all_motors_speed(0)
    print('over')
