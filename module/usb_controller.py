import subprocess
import warnings


def reload_all_usb_devices(shut_down_delay: int = 50, boot_delay: int = 500, print_details: bool = True) -> None:
    # 运行sudo命令
    usb_hub_vid = '2109:3431'
    command = f" sudo uhubctl -n {usb_hub_vid} -a 0 -w {shut_down_delay}&&sudo uhubctl -n {usb_hub_vid} -a 1 -w {boot_delay}"

    if print_details:
        subprocess.call(command, shell=True)
    else:
        subprocess.call(command, shell=True, stdout=subprocess.DEVNULL)

    # 打印输出结果
    warnings.warn('>>>USB devices Reloaded<<<\n'
                  '##########################')
