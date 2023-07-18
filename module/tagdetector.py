from multiprocessing import Process
import time
import warnings
from time import sleep, time
from typing import Tuple, List, Dict

from .algrithm_tools import calc_p2p_dst
from .camra import Camera
from ..constant import TAG_GROUP

DEFAULT_TAG_ID = -1

NULL_TAG = -999

TABLE_INIT_VALUE = (None, 0.)

CAMERA_RESOLUTION_MULTIPLIER = 0.4

try:
    import cv2
    from apriltag import Detector, DetectorOptions
except ImportError:
    warnings.warn('failed to import vision deps')


def get_center_tag(frame_center: Tuple[int, int], tags: List):
    # 获取离图像中心最近的 AprilTag
    closest_tag = None
    closest_dist = float('inf')
    for tag in tags:
        # 计算当前 AprilTag 中心点与图像中心的距离
        dist = calc_p2p_dst(tag.center, frame_center)
        if dist < closest_dist:
            closest_dist = dist
            closest_tag = tag
    return closest_tag


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

    def __init__(self, camera: Camera, team_color: str, start_detect_tag: bool = True, max_fps: int = 20):
        self._camera: Camera = camera
        self._tags_table: Dict[int, Tuple] = {}
        self._tags: List = []
        self._tag_id: int = DEFAULT_TAG_ID
        self._tag_monitor_switch: bool = False
        self._enemy_tag: int = NULL_TAG
        self._ally_tag: int = NULL_TAG
        self._neutral_tag: int = NULL_TAG
        self._max_fps: int = max_fps

        self.set_tags(team_color)
        self._init_tags_table()
        if start_detect_tag:
            self.apriltag_detect_start()

    def _init_tags_table(self):
        """
        the tags table stores the tag obj and the distance to the camera center
        :return:
        """
        self._tags_table[self._enemy_tag] = TABLE_INIT_VALUE
        self._tags_table[self._ally_tag] = TABLE_INIT_VALUE
        self._tags_table[self._neutral_tag] = TABLE_INIT_VALUE

    def set_tags(self, team_color: str = 'blue'):
        """
        set the ally/enemy tag according the team color

        blue: ally: 1 ; enemy: 2
        yellow: ally: 2 ; enemy: 1
        :param team_color: blue or yellow
        :return:
        """
        self._neutral_tag = 0
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
                                  name="apriltag_detect_Process", kwargs=kwargs)
        apriltag_detect.daemon = True
        apriltag_detect.start()

    def _apriltag_detect_loop(self, single_tag_mode: bool = True):
        """
        这是一个线程函数，它从摄像头捕获视频帧，处理帧以检测 AprilTags，
        :param single_tag_mode: if check only a single tag one time
        :return:
        """

        start_time: float = time()
        fps: int = 0
        while self._camera.latest_read_status:
            if self.tag_monitor_switch:  # 台上开启 台下关闭 节约性能
                self._update_tags()
                self._update_tag_id(single_tag_mode)
                if time() - start_time < 1:
                    # TODO: such fps limiter may not be accurate
                    fps += 1
                    if fps >= self._max_fps:
                        # sleep to the end of second as the fps exceeds the limit
                        time.sleep(1 - time() + start_time)
                else:
                    fps = 0
                    start_time = time()

            else:
                # TODO: This delay may not be correct,since it could cause wrongly activate enemy box action
                sleep(0.4)
        warnings.warn('\n##########CAMERA LOST###########\n'
                      '###ENTERING NO CAMERA MODE###')
        self._tag_id = DEFAULT_TAG_ID

    def _update_tags(self):
        """
        update tags from the newly sampled frame
        :return:
        """
        self._camera.update_frame()
        frame = self._camera.latest_frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 将帧转换为灰度并存储在 gray 变量中。
        # 使用 AprilTag 检测器对象（self.tag_detector）在灰度帧中检测 AprilTags。检测到的标记存储在 self._tags 变量中。
        self._tags: List = self.__tag_detector.detect(gray)
        if self._tags:
            # override old tags
            self._init_tags_table()
            for tag in self._tags:
                self._tags_table[tag.tag_id] = (tag, calc_p2p_dst(tag.center, self._camera.frame_center))

    def _update_tag_id(self, single_tag_mode):
        """
        update the tag id from the self._tags_table
        :param single_tag_mode:
        :return:
        """

        def single_mode():
            self._tag_id = DEFAULT_TAG_ID
            for tag_data in self._tags_table.values():
                if tag_data[0]:
                    self._tag_id = tag_data[0].tag_id
                    break

        def nearest_mode():
            closest_dist = float('inf')
            closest_tag = None
            for tag_data in self._tags_table.values():
                # check the tag obj is valid and compare with the closest tag
                if tag_data[0] and tag_data[1] < closest_dist:
                    closest_dist = tag_data[1]
                    closest_tag = tag_data[0]
            self._tag_id = closest_tag.tag_id if closest_tag else DEFAULT_TAG_ID

        if single_tag_mode:
            single_mode()
        else:
            nearest_mode()

    @property
    def tag_table(self):
        return self._tags_table

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
            self._tag_id = DEFAULT_TAG_ID

    @property
    def ally_tag(self):
        return self._ally_tag

    @property
    def enemy_tag(self):
        return self._enemy_tag
