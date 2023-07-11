import os
from threading import Thread
import time
from time import sleep
from typing import List, Tuple, Optional, Sequence, ByteString
from .serial_helper import SerialHelper
from ..constant import ENV_CACHE_DIR_PATH

cache_dir = os.environ.get(ENV_CACHE_DIR_PATH)


class CloseLoopController:

    def __init__(self, motor_ids: Tuple[int, int, int, int], motor_dirs: Tuple[int, int, int, int],
                 port: Optional[str] = 'tty/USB0', debug: bool = False):
        """
        :param motor_dirs:
        :param motor_ids: the id of the motor,represent as follows [fl,rl,rr,fr]
        """
        self._debug: bool = debug
        # 创建串口对象
        self._serial: SerialHelper = SerialHelper(port=port, con2port_when_created=True, auto_search_port=True)
        if self._debug:
            def serial_handler(data: ByteString):
                print(data)

            self._serial.set_on_data_received_handler(serial_handler)
            self._serial.start_read_thread()
        # 发送的数据队列
        self._motor_speeds: Tuple[int, int, int, int] = (0, 0, 0, 0)
        self._motor_ids: Tuple[int, int, int, int] = motor_ids
        self._motor_dirs: Tuple[int, int, int, int] = motor_dirs
        self._cmd_list: List[ByteString] = [makeCmd('RESET')]
        self._hang_time_list: List[float] = [0.]

        self._msg_send_thread: Optional[Thread] = None
        self._start_msg_sending()

    @property
    def motor_ids(self) -> Tuple[int, int, int, int]:
        return self._motor_ids

    @property
    def motor_speeds(self) -> Tuple[int, int, int, int]:
        return self._motor_speeds

    @property
    def motor_dirs(self) -> Tuple[int, int, int, int]:
        return self._motor_dirs

    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, debug: bool):
        self._debug = debug

    def _start_msg_sending(self) -> None:
        # 通信线程创建启动
        self._msg_send_thread = Thread(name="msg_send_thread", target=self._msg_sending_loop)
        self._msg_send_thread.daemon = True
        self._msg_send_thread.start()

    def _msg_sending_loop(self) -> None:
        """
        串口通信线程发送函数
        :return:
        """
        print(f"msg_sending_thread_start, the debugger is [{self._debug}]")

        def sending_loop() -> None:
            while True:
                if self._cmd_list:
                    self._serial.write(self._cmd_list.pop(0))
                    if self._hang_time_list:
                        sleep(self._hang_time_list.pop(0))

        def sending_loop_debugging() -> None:
            while True:
                if self._cmd_list:
                    temp = self._cmd_list.pop(0)
                    print(f'\nwriting {temp} to channel,remaining {len(self._cmd_list)}')
                    self._serial.write(temp)
                    if self._hang_time_list:
                        sleep(self._hang_time_list.pop(0))

        if self._debug:
            sending_loop_debugging()
        else:
            sending_loop()

    def makeCmds_dirs(self, speed_list: Tuple[int, int, int, int]) -> ByteString:
        """
        make the cmd according to speed_list and direction list
        :param speed_list:
        :return:
        """
        return makeCmd_list([f'{motor_id}v{speed * direction}'
                             for motor_id, speed, direction in
                             zip(self._motor_ids, speed_list, self._motor_dirs)])

    def append_to_stack(self, byte_string: ByteString, hang_time: float = 0.):
        """
        push the given byte string onto the stack
        :param hang_time:the time during which the cmd sender will hang up , to release the cpu
        :param byte_string:the string to write to the cmd_list
        :return:
        """
        self._cmd_list.append(byte_string)
        if hang_time:
            self._hang_time_list.append(hang_time)

    def move_cmd(self, left_speed: int, right_speed: int) -> None:
        """
        control the motor
        :param left_speed:
        :param right_speed:
        :return:
        """
        self._motor_speeds = (left_speed, left_speed, right_speed, right_speed)
        self.set_motors_speed(self._motor_speeds)

    def set_motors_speed(self, speed_list: Tuple[int, int, int, int], hang_time: float = 0.) -> None:
        """
        set the speed of the motor to the given speed, and hang up the cmd sender to release the cpu
        will check if the desired speed is already requested
        will make sure the direction is same with direction list
        :param speed_list: the motor speed
        :param hang_time:
        :return:
        """
        self._motor_speeds = speed_list
        if is_list_all_zero(self._motor_speeds):
            self.set_all_motors_speed(0, hang_time=hang_time)
        else:
            # will check the if target speed and current speed are the same and can customize the direction
            cmd_list = [f'{motor_id}v{speed * direction}'
                        for motor_id, speed, cur_speed, direction in
                        zip(self._motor_ids, self._motor_speeds, self._motor_speeds, self._motor_dirs)
                        if speed != cur_speed]

            if cmd_list:
                self.append_to_stack(byte_string=makeCmd_list(cmd_list), hang_time=hang_time)

    def set_all_motors_speed(self, speed: int, hang_time: float = 0.) -> None:
        """
        set all motors speed ,and hang up the cmd sender
        :attention: this function has no direction check, since it will be a broadcast cmd
        :param speed:
        :param hang_time:
        :return:
        """
        self.append_to_stack(byte_string=makeCmd(f'v{speed}'), hang_time=hang_time)
        self._motor_speeds = (speed, speed, speed, speed)

    def open_userInput_channel(self, debug: bool = False) -> None:
        """
        open a user input channel for direct access to the driver
        :return:
        """

        ct = 0
        print('\n\nuser input channel opened\nplease enter cmd below,enter [exit] to end the channel')
        debug_temp = self._debug
        self._debug = debug
        if self._debug:
            self._serial.start_read_thread()

            def handler(data: ByteString):
                print(f'\nout[{ct}]: {data}')

            self._serial.set_on_data_received_handler(handler)
        while True:
            user_input = input(f'\rin[{ct}]: ')
            ct += 1
            # 对输入的内容进行处理
            if user_input == 'exit':
                print('\nuser input channel closed')
                self._debug = debug_temp
                break
            else:
                self.append_to_stack(byte_string=makeCmd(user_input))


def is_list_all_zero(lst: Sequence[int]) -> bool:
    return all(element == 0 for element in lst)


def is_rotate_cmd(lst: Tuple[int, int, int, int]) -> bool:
    return lst[0] == lst[1] and lst[2] == lst[3] and lst[0] + lst[2] == 0


def makeCmd_list(cmd_list: List[str]) -> ByteString:
    """
    encode a list of cmd strings into a single bstring
    :param cmd_list:
    :return:
    """
    return b''.join(cmd.encode('ascii') + b'\r' for cmd in cmd_list)


def makeCmd(cmd: str) -> ByteString:
    """
    encode a cmd to a bstring
    :param cmd:
    :return:
    """
    return cmd.encode('ascii') + b'\r'


def motor_speed_test(speed_level: int = 11, interval: float = 1, using_id: bool = True, laps: int = 3) -> None:
    """
    motor speed test function,used to test and check  if the driver configurations are correct
    :param speed_level:
    :param interval:
    :param using_id:
    :param laps:
    :return:
    """
    con = CloseLoopController(motor_ids=(4, 3, 1, 2), motor_dirs=(-1, -1, 1, 1))
    try:
        for _ in range(laps):
            if using_id:
                for i in range(speed_level):
                    print(f'doing {i * 1000}')
                    con.set_motors_speed((1000 * i, 1000 * i, 1000 * i, 1000 * i))
                    time.sleep(interval)
            else:
                for i in range(speed_level):
                    print(f'doing {i * 1000}')
                    con.set_all_motors_speed(i * 1000)
                    time.sleep(interval)
    finally:
        con.set_all_motors_speed(0)
    print('over')
