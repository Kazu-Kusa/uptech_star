import subprocess
import warnings


def reload_uart_device(shut_down_delay: int = 200, boot_delay: int = 400, print_details: bool = False) -> None:
    """
    primarily used to reset the uart device since it can't handle exceptions on run,
    will repower the usb device using uhubctl
    :param shut_down_delay:
    :param boot_delay:
    :param print_details:
    :return:
    """
    # 运行sudo命令
    device_location = '1-1'
    port = '2'
    command = f"sudo uhubctl -a 0 -p {port} -l {device_location} -w {shut_down_delay}&&" \
              f"sudo rm -rf /dev/ttyUSB0&&" \
              f"sudo uhubctl -a 1 -p {port} -l {device_location} -w {boot_delay}"

    if print_details:
        subprocess.call(command, shell=True)
    else:
        subprocess.call(command, shell=True, stdout=subprocess.DEVNULL)

    # 打印输出结果
    warnings.warn('>>>USB devices Reloaded<<<\n'
                  '##########################')
