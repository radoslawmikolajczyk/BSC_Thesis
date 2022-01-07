import numpy as np
import cv2 as cv
import glob

criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
objp = np.zeros((6 * 8, 3), np.float32)
objp[:, :2] = np.mgrid[0:8, 0:6].T.reshape(-1, 2)
objpoints = []
imgpoints = []
images = glob.glob('images/*.jpg')

for fname in images:
    img = cv.imread(fname)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    ret, corners = cv.findChessboardCorners(gray, (8, 6), None)
    if ret:
        objpoints.append(objp)
        corners2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners)
        cv.drawChessboardCorners(img, (8, 6), corners2, ret)
cv.destroyAllWindows()

ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
np.savez('calibration.npz', matrix=mtx, distortion=dist, rotation_vectors=rvecs, translation_vectors=tvecs)

data = np.load('calibration.npz')
img = cv.imread('not_calibrated.jpg')
h, w = img.shape[:2]
new_camera_mtx, roi = cv.getOptimalNewCameraMatrix(data['matrix'], data['distortion'], (w, h), 0, (w, h))

dst = cv.undistort(img, data['matrix'], data['distortion'], None, new_camera_mtx)
x, y, w, h = roi
dst = dst[y:y + h, x:x + w]
cv.imwrite('calibration_result.jpg', dst)
