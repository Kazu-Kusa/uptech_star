def is_tilted(roll: float, pitch: float, threshold=45):
    """
    判断当前姿态是否倾倒

    :param roll: 横滚角，单位为度
    :param pitch: 俯仰角，单位为度
    :param threshold: 倾倒阈值，超过此角度则判断为倾倒，默认为45度
    :return: True代表倾倒，False代表未倾倒
    """
    return abs(roll) > threshold or abs(pitch) > threshold
