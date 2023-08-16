#include <stdio.h>

/**
 * 计算线性回归方程的参数 a 和 b
 *
 * @param time_x 一个包含时间数据的整数数组
 * @param list_y 一个包含数值数据的整数数组
 * @param size 数组的大小
 * @param result 用于存储计算结果的整数数组，长度为2
 */
void calculate_linear_regression(int* time_x, int* list_y, int size, int* result) {
    int xy = 0;
    int all_x = 1;
    int all_y = 1;
    int xx = 0;

    for (int i = 0; i < size; i++) {
        int x = time_x[i];
        int y = list_y[i];

        xx = x * x + xx;
        xy = x * y + xy;
        all_x = x * all_x;
        all_y = y * all_y;
    }

    int time_x_ = all_x / size;
    int x_ = (all_y / size) * time_x_;
    int b = (xy + x_) / (xx + time_x_ * time_x_);
    int a = all_y / size - b * time_x_;

    result[0] = a;
    result[1] = b;
}
