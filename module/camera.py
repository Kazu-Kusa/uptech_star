from multiprocessing import Process
import time
import warnings
from time import sleep

from ..constant import TAG_GROUP

try:
    import cv2
    from apriltag import Detector, DetectorOptions
except ImportError:
    warnings.warn('failed to import vision deps')


class Camera(object):
    __tag_detector = Detector(DetectorOptions(families=TAG_GROUP)).detect

    # 使用 cv2.VideoCapture(0) 创建视频捕获对象，从默认摄像头捕获视频。
    __cap = cv2.VideoCapture(0)
    if __cap is None:
        warnings.warn('########CAN\'T GET VIDEO########\n')
    else:
        width = __cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = __cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"CAMERA RESOLUTION：{int(width)}x{int(height)}")

    def __init__(self, team_color: str = '', start_detect_tag: bool = True):
        self._tag_id: int = -1
        self._tag_monitor_switch: bool = True
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

    def _apriltag_detect_loop(self, single_tag_mode: bool = True, print_tag_id: bool = False,
                              check_interval: float = 0.1):
        """
        这是一个线程函数，它从摄像头捕获视频帧，处理帧以检测 AprilTags，
        :param check_interval:
        :param single_tag_mode: if check only a single tag one time
        :param print_tag_id: if print tag id on check
        :return:
        """
        print_interval: float = 1.2
        try:

            start_time = time.time()
            while True:

                if self.tag_monitor_switch:  # 台上开启 台下关闭 节约性能
                    # 在循环内，从视频捕获对象中捕获帧并将其存储在 frame 变量中。然后将帧裁剪为中心区域的 weight x weight 大小。
                    ret, frame = self.__cap.read()
                    # TODO: open the crop and resize options to users
                    if not ret:
                        warnings.warn('\n##########CAMERA LOST###########\n'
                                      '###ENTERING NO CAMERA MODE###')
                        self._tag_id = -1
                        break
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 将帧转换为灰度并存储在 gray 变量中。
                    # 使用 AprilTag 检测器对象（self.tag_detector）在灰度帧中检测 AprilTags。检测到的标记存储在 tags 变量中。
                    tags = self.__tag_detector(gray)
                    if tags:
                        if single_tag_mode:
                            self._tag_id = tags[0].tag_id
                        else:
                            # 获取离图像中心最近的 AprilTag
                            closest_tag = None
                            closest_dist = float('inf')
                            for tag in tags:
                                # 计算当前 AprilTag 的中心点
                                center = tag.center
                                # 计算当前 AprilTag 中心点与图像中心的距离
                                dist = ((center[0] - frame.shape[1] / 2) ** 2 + (
                                        center[1] - frame.shape[0] / 2) ** 2) ** 0.5
                                if dist < closest_dist:
                                    closest_dist = dist
                                    closest_tag = tag
                            self._tag_id = closest_tag if closest_tag else tags[0].tag_id
                        if print_tag_id and time.time() - start_time > print_interval:
                            print(f"#DETECTED TAG: [{self._tag_id}]")
                            start_time = time.time()
                    else:
                        # if not tags detected,return to default
                        self._tag_id = -1
                    sleep(check_interval)
                else:
                    # TODO: This delay may not be correct,since it could cause wrongly activate enemy box action
                    sleep(0.6)

        except:
            warnings.warn("###CAM ERROR###")
            return

        # endregion

        # region properties

    @property
    def camera_is_on(self):
        return bool(self.__cap)

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
        self._tag_id = -1
        self._tag_monitor_switch = switch

    @property
    def ally_tag(self):
        return self._ally_tag

    @property
    def enemy_tag(self):
        return self._enemy_tag
