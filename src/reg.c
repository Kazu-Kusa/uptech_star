#include <stdio.h>

int compute(float* time_x, float* list_y, int length) {
    float all_x = 0;  // 所有x相加
    float all_y = 0;  // 所有y相加
    float xx = 0;  // 所有x的平方相加
    float xy = 0;  // 所有x*y相加
    float time_x_ = 0;  // 平均x
    float time_y_ = 0;  // 平均y
    float nxy_ = 0;  // 平均数x与平均y相乘后乘以n
    float nxx_ = 0;  // 平均数x与平均x相乘后乘以n
    float b = 0;  // 斜率
    float a = 0;  // 差值
    float infer_y = 0;

    for (int i = 0; i < length; i++) {
        xx = time_x[i] * time_x[i] + xx;
        xy = time_x[i] * list_y[i] + xy;
        all_x = time_x[i] + all_x;
        all_y = list_y[i] + all_y;
    }

    time_x_ = all_x / length;  // 平均x
    time_y_ = all_y / length;  // 平均y
    nxy_ = time_x_ * time_y_ * length;  // 平均数x与平均y相乘后乘以n
    nxx_ = time_x_ * time_x_ * length;  // 平均数x与平均x相乘后乘以n
    b = (xy - nxy_) / (xx - nxx_);  // 斜率
    a = all_y / length - b * time_x_;  // 差值
    infer_y = a + b * (length + 1);

    return infer_y;
}

