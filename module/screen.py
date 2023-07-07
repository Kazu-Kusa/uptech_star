import warnings

from .uptech import load_lib


class Screen(object):
    try:
        so_up = load_lib('libuptech.so')
    except OSError:
        warnings.warn('##Screen: Failed to load libuptech.so##')
    # region font size definitions
    FONT_4X6 = 0
    FONT_5X8 = 1
    FONT_5X12 = 2
    FONT_6X8 = 3
    FONT_6X10 = 4
    FONT_7X12 = 5
    FONT_8X8 = 6
    FONT_8X12 = 7
    FONT_8X14 = 8
    FONT_10X16 = 9
    FONT_12X16 = 10
    FONT_12X20 = 11
    FONT_16X26 = 12
    FONT_22X36 = 13
    FONT_24X40 = 14
    # endregion

    # region color Hex value
    COLOR_WHITE = 0xFFFF
    COLOR_BLACK = 0x0000
    COLOR_BLUE = 0x001F
    COLOR_BRED = 0XF81F
    COLOR_GRED = 0XFFE0
    COLOR_GBLUE = 0X07FF
    COLOR_RED = 0xF800
    COLOR_MAGENTA = 0xF81F
    COLOR_GREEN = 0x07E0
    COLOR_CYAN = 0x7FFF
    COLOR_YELLOW = 0xFFE0
    COLOR_BROWN = 0XBC40
    COLOR_BRRED = 0XFC07
    COLOR_GRAY = 0X8430
    COLOR_DARKBLUE = 0X01CF
    COLOR_LIGHTBLUE = 0X7D7C
    COLOR_GRAYBLUE = 0X5458
    COLOR_LIGHTGREEN = 0X841F
    COLOR_LGRAY = 0XC618
    COLOR_LGRAYBLUE = 0XA651
    COLOR_LBBLUE = 0X2B12

    # endregion

    def __init__(self, init_screen: bool = True):
        if init_screen:
            self.LCD_Open()
            self.LCD_FillScreen(self.COLOR_BLACK)
            self.LCD_Refresh()

    def LCD_Open(self, direction: int = 2):
        """
        open with lcd ,and set the LCD displaying direction

        1 for vertical, 2 for horizontal
        """
        assert direction == 1 or direction == 2, "1 for vertical and 2 for horizontal"

        return self.so_up.lcd_open(direction)

    def LCD_Refresh(self):
        """
        clear the displayed contents
        """
        self.so_up.LCD_Refresh()

    def LCD_SetFontSize(self, font_size: int):
        self.so_up.LCD_SetFont(font_size)

    def LCD_SetForeColor(self, color: int):
        """
        set the fore color
        """
        self.so_up.UG_SetForecolor(color)

    def LCD_SetBackColor(self, color: int):
        """
        set the LCD background color
        """
        self.so_up.UG_SetBackcolor(color)

    def LCD_FillScreen(self, color: int):
        """
        fill the screen with the given color
        """
        self.so_up.UG_FillScreen(color)

    def LCD_PutString(self, x: int, y: int, display_string: str):
        """
        x,y(unit:pixel) are the coordinates of where the string that will be displayed

        display_string is  string that will be displayed in the LCD

        """
        self.so_up.UG_PutString(x, y, display_string.encode())

    def LCD_FillFrame(self, x1, y1, x2, y2, color: int):
        self.so_up.UG_FillFrame(x1, y1, x2, y2, color)

    def LCD_FillRoundFrame(self, x1, y1, x2, y2, r, color: int):
        self.so_up.UG_FillRoundFrame(x1, y1, x2, y2, r, color)

    def LCD_DrawMesh(self, x1, y1, x2, y2, color: int):
        self.so_up.UG_DrawMesh(x1, y1, x2, y2, color)

    def LCD_DrawFrame(self, x1, y1, x2, y2, color: int):
        self.so_up.UG_DrawFrame(x1, y1, x2, y2, color)

    def LCD_DrawRoundFrame(self, x1, y1, x2, y2, r, color: int):
        self.so_up.UG_DrawRoundFrame(x1, y1, x2, y2, r, color)

    def LCD_DrawPixel(self, x0, y0, color: int):
        self.so_up.UG_DrawPixel(x0, y0, color)

    def LCD_DrawCircle(self, x0, y0, r, color: int):
        self.so_up.UG_DrawCircle(x0, y0, r, color)

    def LCD_FillCircle(self, x0, y0, r, color: int):
        self.so_up.UG_FillCircle(x0, y0, r, color)

    def LCD_DrawArc(self, x0, y0, r, s, color: int):
        self.so_up.UG_DrawArc(x0, y0, r, s, color)

    def LCD_DrawLine(self, x1, y1, x2, y2, color: int):
        self.so_up.UG_DrawLine(x1, y1, x2, y2, color)

    def ADC_Led_SetColor(self, index: int, color: int):
        """
        set the color of the LED according to index and color
        """
        self.so_up.adc_led_set(index, color)


if __name__ == '__main__':
    pass
