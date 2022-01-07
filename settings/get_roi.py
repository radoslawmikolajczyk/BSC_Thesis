import numpy as np
import cv2 as cv

data = np.load('calibration.npz')
img = cv.imread('not_calibrated.jpg')
h, w = img.shape[:2]
new_camera_mtx, roi = cv.getOptimalNewCameraMatrix(data['matrix'], data['distortion'], (w, h), 0, (w, h))

dst = cv.undistort(img, data['matrix'], data['distortion'], None, new_camera_mtx)
x, y, w, h = roi
dst = dst[y:y + h, x:x + w]
cv.imwrite('calibration_result.jpg', dst)