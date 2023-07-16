import cv2
import numpy as np
from numpy import xrange


def rotate90(src: np.ndarray) -> np.ndarray:
    """
    旋转图像90度，使之以顺时针方向旋转90度。

    :param src: 原始图像数据，类型为np.ndarray。
    :return: 顺时针旋转90度后的图像数据，类型为np.ndarray。
    """
    r_Img = cv2.rotate(src, cv2.ROTATE_90_CLOCKWISE)
    return r_Img


def rotate180(src: np.ndarray) -> np.ndarray:
    """
    旋转图像180度，使之上下颠倒或左右翻转。

    :param src: 原始图像数据，类型为np.ndarray。
    :return: 上下颠倒或左右翻转后的图像数据，类型为np.ndarray。
    """
    r_Img = cv2.rotate(src, cv2.ROTATE_180)
    return r_Img


def resize(src: np.ndarray, scale_percent: float) -> np.ndarray:
    """
    按比例缩放图像，通常用于降低图像分辨率。

    :param src: 原始图像数据，类型为np.ndarray。
    :param scale_percent: 缩放比例，控制图像变小的程度。取值范围为[0,100]。
    :return: 缩放后的图像数据，类型为np.ndarray。
    """
    return cv2.resize(src, dsize=None, fx=scale_percent, fy=scale_percent, interpolation=cv2.INTER_AREA)


def calcGrayHist(src: np.ndarray) -> np.ndarray:
    """
    计算灰度图像直方图。

    :param src: 原始图像数据，类型为np.ndarray。
    :return: 灰度图像直方图，类型为np.ndarray。
    """
    rows, cols = src.shape
    grayHist = np.zeros([256], np.uint64)
    for r in xrange(rows):
        for c in xrange(cols):
            grayHist[src[r][c]] += 1
    return grayHist


def linear_trans(src: np.ndarray, alpha: float) -> np.ndarray:
    """
    进行线性变换，增加或降低图像亮度。

    :param src: 原始图像数据，类型为np.ndarray。
    :param alpha: 系数，控制亮度的变化。取值范围为[0.0, 1.0]，当alpha > 1.0时，会增加亮度；若0 < alpha < 1.0，则会降低亮度。
    :return: 线性变换后的图像数据，类型为np.ndarray。
    """
    r_Img = alpha * src
    r_Img[r_Img > 255] = 255
    r_Img = np.round(r_Img)
    r_Img = r_Img.astype(np.uint8)
    return r_Img


def normalize(src: np.ndarray) -> np.ndarray:
    """
    对图像进行归一化处理，使其像素值在指定区间内。

    :param src: 原始图像数据，类型为np.ndarray。
    :return: 归一化处理后的图像数据，类型为np.ndarray。
    """
    r_Img = cv2.normalize(src, 255, 0, cv2.NORM_MINMAX, cv2.CV_8U)
    return r_Img


def gamma_correct(src: np.ndarray) -> np.ndarray:
    """
    伽马校正，将输入图像灰度值映射到更均匀的分布。
    :param src: 输入的灰度图像，像素值取值范围 [0, 255]
    :return: 处理后的灰度图像，像素值取值范围 [0, 1.0]
    """
    fI = src / 255.0
    gamma = 0.5
    r_Img = np.power(fI, gamma)
    return r_Img.astype(np.float32)


def create_clahe(src: np.ndarray) -> np.ndarray:
    """
    创建自适应直方图均衡化器，并对输入图像进行直方图均衡化处理。
    :param src: 输入的灰度图像，像素值取值范围 [0, 255]
    :return: 处理后的灰度图像，像素值取值范围 [0, 255]
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    dst = clahe.apply(src)
    return dst


def threshold(src: np.ndarray, the: float, maxval: float = 255) -> np.ndarray:
    """
    将输入图像按阈值二值化。
    :param src: 输入的灰度图像，像素值取值范围 [0, 255]
    :param the: 阈值，单通道浮点数或整数
    :param maxval: 设定的输出二值图像的最大值，必须是正数。
    :return: 处理后的二值图像，像素值取值范围 [0, maxval]
    """
    if the == 0:
        otsuThe = 0
        otsuThe, dst = cv2.threshold(src, otsuThe, maxval, cv2.THRESH_OTSU)
    else:
        dst = cv2.threshold(src, the, maxval, cv2.THRESH_BINARY)
    return dst


def adaptiveThresh(src: np.ndarray, winSize: tuple[int, int], ratio: float = 0.15) -> np.ndarray:
    """
    Performs adaptive thresholding on the input image `src` using a local mean of `winSize` and a ratio `ratio`.

    Parameters:
        src (np.ndarray): Input D-dimensional single-channel array.
        winSize (tuple[int, int]): Size of the window used to calculate the local mean.
        ratio (float): Thresholding ratio, between 0 and 1. Default is 0.15.

    Returns:
        (np.ndarray): Output binary image of the same size and type as `src`.
    """

    I_mean = cv2.boxFilter(src, cv2.CV_32FC1, winSize)
    out = src - (1.0 - ratio) * I_mean
    out[out >= 0] = 255
    out[out < 0] = 0
    out = out.astype(np.uint8)
    return out


def morphologyEx(src: np.ndarray, r: int, i: int, type: int) -> np.ndarray:
    """
    Applies morphological operations to the input image `src` using a rectangular structuring element of size `(2 * r + 1, 2 * r + 1)`
    and `i` iterations. The type of operation can be specified with the `type` parameter, where `type=0` specifies opening
    and `type=1` specifies closing.

    Parameters:
        src (np.ndarray): Input image of any dimension and type.
        r (int): Size of the structuring element, i.e., half the size on each side of the central pixel.
        i (int): Number of times to perform the specified morphological operation.
        type (int): Type of morphological operation to perform.
                    `type=0` for opening and `type=1` for closing.

    Returns:
        (np.ndarray): Output image of the same size and type as `src`.
    """

    if type == 0:
        s = cv2.getStructuringElement(cv2.MORPH_RECT, (2 * r + 1, 2 * r + 1))
        d = cv2.morphologyEx(src, cv2.MORPH_OPEN, s, iterations=i)
    elif type == 1:
        s = cv2.getStructuringElement(cv2.MORPH_RECT, (2 * r + 1, 2 * r + 1))
        d = cv2.morphologyEx(src, cv2.MORPH_CLOSE, s, iterations=i)
    return d
