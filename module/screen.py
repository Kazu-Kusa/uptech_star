import warnings

from .os_tools import load_lib


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

    FONTS = (
        FONT_4X6, FONT_5X8, FONT_5X12, FONT_6X8,
        FONT_6X10, FONT_7X12, FONT_8X8, FONT_8X12,
        FONT_8X14, FONT_10X16, FONT_12X16, FONT_12X16,
        FONT_16X26, FONT_22X36, FONT_24X40

    )
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

    COLORS = (
        COLOR_WHITE, COLOR_BLACK, COLOR_BLUE, COLOR_BRED, COLOR_GRED,
        COLOR_GBLUE, COLOR_RED, COLOR_MAGENTA, COLOR_GREEN, COLOR_CYAN,
        COLOR_YELLOW, COLOR_BROWN, COLOR_BRRED, COLOR_GRAY, COLOR_DARKBLUE,
        COLOR_LIGHTBLUE, COLOR_GRAYBLUE, COLOR_LIGHTGREEN, COLOR_LGRAY,
        COLOR_LGRAYBLUE, COLOR_LBBLUE
    )

    # endregion

    def __init__(self, init_screen: bool = True):
        if init_screen:
            Screen.open()
            Screen.fill_screen(Screen.COLOR_BLACK)
            Screen.refresh()

    @staticmethod
    def open(direction: int = 2):
        """
        open with lcd ,and set the LCD displaying direction

        1 for vertical, 2 for horizontal
        """
        assert direction == 1 or direction == 2, "1 for vertical and 2 for horizontal"

        return Screen.so_up.lcd_open(direction)

    @staticmethod
    def refresh():
        """
        clear the displayed contents
        """
        Screen.so_up.LCD_Refresh()

    @staticmethod
    def set_font_size(font_size: int):
        Screen.so_up.LCD_SetFont(font_size)

    @staticmethod
    def set_fore_color(color: int):
        """
        set the fore color
        """
        Screen.so_up.UG_SetForecolor(color)

    @staticmethod
    def set_back_color(color: int):
        """
        set the LCD background color
        """
        Screen.so_up.UG_SetBackcolor(color)

    @staticmethod
    def set_led_color(index: int, color: int):
        """
        set the color of the LED according to index and color
        """
        Screen.so_up.adc_led_set(index, color)

    @staticmethod
    def fill_screen(color: int):
        """
        fill the screen with the given color
        """
        Screen.so_up.UG_FillScreen(color)

    @staticmethod
    def put_string(x: int, y: int, display_string: str):
        """
        x,y(unit:pixel) are the coordinates of where the string that will be displayed

        display_string is  string that will be displayed in the LCD

        """
        Screen.so_up.UG_PutString(x, y, display_string.encode())

    @staticmethod
    def fill_frame(x1, y1, x2, y2, color: int):
        Screen.so_up.UG_FillFrame(x1, y1, x2, y2, color)

    @staticmethod
    def fill_round_frame(x1, y1, x2, y2, r, color: int):
        Screen.so_up.UG_FillRoundFrame(x1, y1, x2, y2, r, color)

    @staticmethod
    def fill_circle(x0, y0, r, color: int):
        Screen.so_up.UG_FillCircle(x0, y0, r, color)

    @staticmethod
    def draw_mesh(x1, y1, x2, y2, color: int):
        Screen.so_up.UG_DrawMesh(x1, y1, x2, y2, color)

    @staticmethod
    def draw_frame(x1, y1, x2, y2, color: int):
        Screen.so_up.UG_DrawFrame(x1, y1, x2, y2, color)

    @staticmethod
    def draw_round_frame(x1, y1, x2, y2, r, color: int):
        Screen.so_up.UG_DrawRoundFrame(x1, y1, x2, y2, r, color)

    @staticmethod
    def draw_pixel(x0, y0, color: int):
        Screen.so_up.UG_DrawPixel(x0, y0, color)

    @staticmethod
    def draw_circle(x0, y0, r, color: int):
        Screen.so_up.UG_DrawCircle(x0, y0, r, color)

    @staticmethod
    def draw_arc(x0: int, y0: int, r, s, color: int):
        Screen.so_up.UG_DrawArc(x0, y0, r, s, color)

    @staticmethod
    def draw_line(x1: int, y1: int, x2: int, y2: int, color: int):
        Screen.so_up.UG_DrawLine(x1, y1, x2, y2, color)


if __name__ == '__main__':
    pass
