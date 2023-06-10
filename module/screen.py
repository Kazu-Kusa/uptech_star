import ctypes
from .uptech import so_up


class Screen(object):
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

    @staticmethod
    def LCD_Open(direction: int = 2):
        """
        open with lcd ,and set the LCD displaying direction

        1 for vertical, 2 for horizontal
        """
        assert direction == 1 or direction == 2, "1 for vertical and 2 for horizontal"

        return so_up.lcd_open(direction)

    @staticmethod
    def LCD_Refresh():
        """
        clear the displayed contents
        """
        so_up.LCD_Refresh()

    @staticmethod
    def LCD_SetFontSize(font_size: int):
        so_up.LCD_SetFont(font_size)

    @staticmethod
    def LCD_SetForeColor(color: int):
        """
        set the fore color
        """
        so_up.UG_SetForecolor(color)

    @staticmethod
    def LCD_SetBackColor(color: int):
        """
        set the LCD background color
        """
        so_up.UG_SetBackcolor(color)

    @staticmethod
    def LCD_FillScreen(color: int):
        """
        fill the screen with the given color
        """
        so_up.UG_FillScreen(color)

    @staticmethod
    def LCD_PutString(x: int, y: int, display_string: str):
        """
        x,y(unit:pixel) are the coordinates of where the string that will be displayed

        display_string is  string that will be displayed in the LCD

        """

        # create a c_byte list whose length is the length of the string

        byte = ctypes.c_byte * len(display_string)
        binary = byte()
        for i, char in enumerate(display_string):
            # dump chars to binary as unicode
            binary[i] = ord(char)
        so_up.UG_PutString(x, y, binary)

    @staticmethod
    def LCD_FillFrame(x1, y1, x2, y2, color: int):
        so_up.UG_FillFrame(x1, y1, x2, y2, color)

    @staticmethod
    def LCD_FillRoundFrame(x1, y1, x2, y2, r, color: int):
        so_up.UG_FillRoundFrame(x1, y1, x2, y2, r, color)

    @staticmethod
    def LCD_DrawMesh(x1, y1, x2, y2, color: int):
        so_up.UG_DrawMesh(x1, y1, x2, y2, color)

    @staticmethod
    def LCD_DrawFrame(x1, y1, x2, y2, color: int):
        so_up.UG_DrawFrame(x1, y1, x2, y2, color)

    @staticmethod
    def LCD_DrawRoundFrame(x1, y1, x2, y2, r, color: int):
        so_up.UG_DrawRoundFrame(x1, y1, x2, y2, r, color)

    @staticmethod
    def LCD_DrawPixel(x0, y0, color: int):
        so_up.UG_DrawPixel(x0, y0, color)

    @staticmethod
    def LCD_DrawCircle(x0, y0, r, color: int):
        so_up.UG_DrawCircle(x0, y0, r, color)

    @staticmethod
    def LCD_FillCircle(x0, y0, r, color: int):
        so_up.UG_FillCircle(x0, y0, r, color)

    @staticmethod
    def LCD_DrawArc(x0, y0, r, s, color: int):
        so_up.UG_DrawArc(x0, y0, r, s, color)

    @staticmethod
    def LCD_DrawLine(x1, y1, x2, y2, color: int):
        so_up.UG_DrawLine(x1, y1, x2, y2, color)

    @staticmethod
    def ADC_Led_SetColor(index: int, color: int):
        """
        set the color of the LED according to index and color
        """
        so_up.adc_led_set(index, color)


if __name__ == '__main__':
    pass
