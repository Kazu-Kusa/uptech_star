import uptech
import time

up = uptech.UpTech()

up.LCD_Open(2)
up.ADC_IO_Open()
up.ADC_Led_SetColor(0, 0x000000)
up.ADC_Led_SetColor(1, 0x000000)
up.CDS_Open()
up.CDS_SetMode(1, 0)
up.MPU6500_Open()

up.LCD_PutString(30, 0, 'InnoStarTest')
up.LCD_Refresh()
up.LCD_SetFont(up.FONT_8X14)

count = 0

while True:
    adc_value = up.ADC_Get_All_Channle()
    battery_voltage_float = adc_value[9] * 3.3 * 4.0 / 4096
    str_battery_voltage_float = '%.2fV' % battery_voltage_float

    up.LCD_PutString(0, 16, 'Battery:' + str_battery_voltage_float + '  ')

    attitude = up.MPU6500_GetAttitude()
    str_attitude_pitch = 'Pitch:%.2f  ' % attitude[0]
    str_attitude_roll = 'Roll :%.2f  ' % attitude[1]
    str_attitude_yaw = 'Yaw  :%.2f  ' % attitude[2]

    up.LCD_PutString(0, 30, str_attitude_pitch)
    up.LCD_PutString(0, 44, str_attitude_roll)
    up.LCD_PutString(0, 58, str_attitude_yaw)
    up.LCD_Refresh()

    count += 1

    if count <= 10:
        up.CDS_SetAngle(1, 512, 800)
        up.ADC_Led_SetColor(0, 0x0A0000)
        up.ADC_Led_SetColor(1, 0x0A0000)
    elif count <= 20:
        up.CDS_SetAngle(1, 200, 800)
        up.ADC_Led_SetColor(0, 0x000A00)
        up.ADC_Led_SetColor(1, 0x000A00)
    elif count <= 30:
        up.CDS_SetAngle(1, 512, 800)
        up.ADC_Led_SetColor(0, 0x00000A)
        up.ADC_Led_SetColor(1, 0x00000A)
    elif count <= 40:
        up.CDS_SetAngle(1, 900, 800)
        up.ADC_Led_SetColor(0, 0x080800)
        up.ADC_Led_SetColor(1, 0x080800)
    else:
        count = 0

    time.sleep(0.01)
