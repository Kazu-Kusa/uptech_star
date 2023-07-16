import warnings
from typing import Tuple, Optional

import cv2


class Camera(object):
    # 使用 cv2.VideoCapture(0) 创建视频捕获对象，从默认摄像头捕获视频。
    __camera = cv2.VideoCapture(0)
    __read_status, __frame = __camera.read()
    if __camera and __read_status:
        origin_width: int = __camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        origin_height: int = __camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        __frame_center: Tuple = (int(origin_width / 2), int(origin_height / 2))
        print(f"CAMERA RESOLUTION：{int(origin_width)}x{int(origin_height)}|CAM CENTER: [{__frame_center}]")
    else:
        warnings.warn('########CAN\'T GET VIDEO########\n'
                      'please check if the camera is attached!')

    @classmethod
    def update_cam_center(cls) -> None:
        width = cls.__camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cls.__camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        cls.__frame_center = (int(width / 2), int(height / 2))

    @classmethod
    def get_frame_center(cls) -> Tuple[int, int]:
        return cls.__frame_center

    @classmethod
    def set_cam_resolution(cls, new_width: Optional[int] = None, new_height: Optional[int] = None,
                           multiplier: Optional[float] = None) -> None:
        assert (new_width is not None and new_height is not None) or (
                multiplier is not None), 'Please specify the resolution params'
        if multiplier:
            cls.__camera.set(cv2.CAP_PROP_FRAME_WIDTH, int(multiplier * cls.origin_width))
            cls.__camera.set(cv2.CAP_PROP_FRAME_HEIGHT, int(multiplier * cls.origin_height))
        else:
            cls.__camera.set(cv2.CAP_PROP_FRAME_WIDTH, new_width)
            cls.__camera.set(cv2.CAP_PROP_FRAME_HEIGHT, new_height)
        cls.update_cam_center()

    @classmethod
    def update_frame(cls) -> None:
        cls.__read_status, cls.__frame = cls.__camera.read()

    @classmethod
    def get_latest_read_status(cls) -> bool:
        return cls.__read_status

    @classmethod
    def get_latest_frame(cls):
        return cls.__frame

    @classmethod
    def get_camera_device(cls) -> cv2.VideoCapture:
        return cls.__camera
