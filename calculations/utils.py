from abc import ABC, abstractmethod
import numpy as np
import cv2
import os


class Calculation(ABC):

    @abstractmethod
    def calculate(self, data):
        pass

    @abstractmethod
    def save_results(self):
        pass


def calculate_distance(p1, p2, roi, frame_height, frame_width):
    src = np.float32(np.array(roi[:4]))
    dst = np.float32([[0, frame_height], [frame_width, frame_height], [frame_width, 0], [0, 0]])
    perspective_transform = cv2.getPerspectiveTransform(src, dst)

    pts = np.float32(np.array([roi[4:7]]))
    warped_pt = cv2.perspectiveTransform(pts, perspective_transform)[0]

    distance_w = np.sqrt((warped_pt[0][0] - warped_pt[1][0]) ** 2 + (warped_pt[0][1] - warped_pt[1][1]) ** 2)
    distance_h = np.sqrt((warped_pt[0][0] - warped_pt[2][0]) ** 2 + (warped_pt[0][1] - warped_pt[2][1]) ** 2)

    h = abs(p2[1] - p1[1])
    w = abs(p2[0] - p1[0])

    dis_w = float((w / distance_w) * 600)
    dis_h = float((h / distance_h) * 600)

    return int(np.sqrt((dis_h ** 2) + (dis_w ** 2)))


def get_frame_details(settings):
    frame_details = cv2.VideoCapture(settings['video_stream'])
    _, frame = frame_details.read()
    w = int(frame_details.get(3))
    h = int(frame_details.get(4))
    frame_details.release()
    calibration_data = np.load(os.getcwd().replace('\\', '/') + '/settings/calibration.npz')
    new_camera_mtx, roi = cv2.getOptimalNewCameraMatrix(calibration_data['matrix'],
                                                        calibration_data['distortion'], (w, h), 0, (w, h))

    dst = cv2.undistort(frame, calibration_data['matrix'], calibration_data['distortion'], None, new_camera_mtx)
    x, y, w, h = roi
    frame = dst[y:y + h, x:x + w]
    f_width, f_height = frame.shape[:2]
    return settings['roi_points'], f_width, f_height
