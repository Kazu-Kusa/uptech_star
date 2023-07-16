from multiprocessing import Process
import time
import warnings
from time import sleep
from typing import Tuple, List

from .camra import Camera
from ..constant import TAG_GROUP

CAMERA_RESOLUTION_MULTIPLIER = 0.4

try:
    import cv2
    from apriltag import Detector, DetectorOptions
except ImportError:
    warnings.warn('failed to import vision deps')


def calc_p2p_dst(point_1: Tuple[int | float, int | float], point_2: Tuple[int | float, int | float]) -> float:
    return ((point_1[0] - point_2[0]) ** 2 + (
            point_1[1] - point_2[1]) ** 2) ** 0.5


class TagDetector:
    __tag_detector = Detector(DetectorOptions(families=TAG_GROUP,
                                              border=1,
                                              nthreads=4,
                                              quad_decimate=1.0,
                                              quad_blur=0.0,
                                              refine_edges=True,
                                              refine_decode=False,
                                              refine_pose=False,
                                              debug=False,
                                              quad_contours=True)).detect

    def __init__(self, team_color: str = '', start_detect_tag: bool = True):
        self._tag_id: int = -1
        self._tag_monitor_switch: bool = False
        self._enemy_tag: int = -999
        self._ally_tag: int = -999

        if team_color:
            self.set_tags(team_color)
        if start_detect_tag:
            self.apriltag_detect_start()

    def set_tags(self, team_color: str = 'blue'):
        """
        set the ally/enemy tag according the team color

        blue: ally: 1 ; enemy: 2
        yellow: ally: 2 ; enemy: 1
        :param team_color: blue or yellow
        :return:
        """
        if team_color == 'blue':
            self._enemy_tag = 2
            self._ally_tag = 1
        elif team_color == 'yellow':
            self._enemy_tag = 1
            self._ally_tag = 2

    def apriltag_detect_start(self, **kwargs):
        """
        start the tag-detection thread and set it to daemon
        :return:
        """
        apriltag_detect = Process(target=self._apriltag_detect_loop,
                                  name="apriltag_detect_detect", kwargs=kwargs)
        apriltag_detect.daemon = True
        apriltag_detect.start()

    def _apriltag_detect_loop(self, single_tag_mode: bool = True,
                              check_interval: float = 0.):
        """
        这是一个线程函数，它从摄像头捕获视频帧，处理帧以检测 AprilTags，
        :param check_interval:
        :param single_tag_mode: if check only a single tag one time
        :return:
        """

        Camera.set_cam_resolution(multiplier=CAMERA_RESOLUTION_MULTIPLIER)
        frame_center = Camera.get_frame_center()
        while Camera.get_latest_read_status():
            if self.tag_monitor_switch:  # 台上开启 台下关闭 节约性能
                # 在循环内，从视频捕获对象中捕获帧并将其存储在 frame 变量中。然后将帧裁剪为中心区域的 weight x weight 大小。
                Camera.update_frame()
                frame = Camera.get_latest_frame()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 将帧转换为灰度并存储在 gray 变量中。
                # 使用 AprilTag 检测器对象（self.tag_detector）在灰度帧中检测 AprilTags。检测到的标记存储在 tags 变量中。
                tags: List = self.__tag_detector.detect(gray)
                if tags:
                    if len(tags) == 1 or single_tag_mode:
                        self._tag_id = tags[0].tag_id
                    else:
                        # 获取离图像中心最近的 AprilTag
                        closest_tag = None
                        closest_dist = float('inf')
                        for tag in tags:
                            # 计算当前 AprilTag 中心点与图像中心的距离
                            dist = calc_p2p_dst(tag.center, frame_center)
                            if dist < closest_dist:
                                closest_dist = dist
                                closest_tag = tag
                        self._tag_id = closest_tag

                else:
                    # if not tags detected,return to default
                    self._tag_id = -1
                sleep(check_interval)
            else:
                # TODO: This delay may not be correct,since it could cause wrongly activate enemy box action
                sleep(0.4)
        warnings.warn('\n##########CAMERA LOST###########\n'
                      '###ENTERING NO CAMERA MODE###')
        self._tag_id = -1

    @property
    def tag_id(self):
        """
        :return:  current tag id
        """
        return self._tag_id

    @property
    def tag_monitor_switch(self):
        return self._tag_monitor_switch

    @tag_monitor_switch.setter
    def tag_monitor_switch(self, switch: bool):
        """
        setter for the switch
        :param switch:
        :return:
        """
        if switch != self._tag_monitor_switch:
            self._tag_monitor_switch = switch
            self._tag_id = -1

    @property
    def ally_tag(self):
        return self._ally_tag

    @property
    def enemy_tag(self):
        return self._enemy_tag
