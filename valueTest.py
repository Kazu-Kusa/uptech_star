import sys
import time

from .uptech import UpTech

up = UpTech()

up.LCD_Open(2)
up.ADC_IO_Open()
up.ADC_Led_SetColor(0, 0x2F0000)
up.ADC_Led_SetColor(1, 0x002F00)

up.LCD_PutString(30, 0, 'InnoStarTest')
up.LCD_Refresh()
# up.LCD_SetFontSize(up.FONT_8X14)

count = 0
sign = 0
io_data = []


def display(mode):
    if mode == 1:
        attitude = up.MPU6500_GetAttitude()
        str_attitude_pitch = 'Pitch:%.2f  ' % attitude[0]
        str_attitude_roll = 'Roll :%.2f  ' % attitude[1]
        str_attitude_yaw = 'Yaw  :%.2f  ' % attitude[2]

        up.LCD_PutString(0, 30, str_attitude_pitch)
        up.LCD_PutString(0, 48, str_attitude_roll)
        up.LCD_PutString(0, 66, str_attitude_yaw)
    elif mode == 2:
        gyro = up.MPU6500_GetGyro()
        str_gyro_1 = f"data 1 {gyro[0]:.2}"
        str_gyro_2 = f"data 2 {gyro[1]:.2}"
        str_gyro_3 = f"data 3 {gyro[2]:.2}"

        up.LCD_PutString(0, 30, str_gyro_1)
        up.LCD_PutString(0, 48, str_gyro_2)
        up.LCD_PutString(0, 66, str_gyro_3)

    elif mode == 3:
        accel = up.MPU6500_GetAccel()

        str_accel_x = f"x :{accel[0]:.2}"
        str_accel_y = f"y :{accel[1]:.2}"
        str_accel_z = f"z :{accel[2]:.2}"

        up.LCD_PutString(0, 30, str_accel_x)
        up.LCD_PutString(0, 44, str_accel_y)
        up.LCD_PutString(0, 54, str_accel_z)
    up.LCD_Refresh()


def read_sensors(mode: int = 1, interval: float = 1):
    while True:
        adc_value = up.ADC_Get_All_Channel()
        battery_voltage_float = adc_value[9] * 3.3 * 4.0 / 4096
        str_battery_voltage_float = '%.2fV' % battery_voltage_float

        up.LCD_PutString(0, 16, 'Battery:' + str_battery_voltage_float + '  ')

        # print(str_battery_voltage_float)

        io_all_input = up.ADC_IO_GetAllInputLevel()
        io_array = '{:08b}'.format(io_all_input)
        io_data.clear()

        display(mode)

        for index, value in enumerate(io_array):
            io = int(value)
            io_data.insert(0, io)

        print("adc_value : ", end="")

        for i in range(len(adc_value) - 1):
            print(f"({i}):", adc_value[i], end=" |")
        print("\n")

        print("io_value : ", end="")

        for i in range(len(io_data)):
            print(f"({i}):", io_data[i], end=" |")
        print("\n")

        time.sleep(interval)
        # if count >= 20:
        #     if sign != 0:
        #         up.CDS_SetAngle(5,0,250)
        #         #up.ADC_Led_Set(0,0x002F00)
        #         up.ADC_Led_SetColor(1,0x2F0000)
        #         sign = 0
        #     else:
        #         up.CDS_SetAngle(5,512,250)
        #         #up.ADC_Led_Set(0,0x2F0000)
        #         up.ADC_Led_SetColor(1,0x002F00)
        #         sign = 1
        #     count = 0
        # else:
        #     count += 1


if __name__ == '__main__':
    read_sensors()
