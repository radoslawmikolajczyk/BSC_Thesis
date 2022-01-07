import cv2
import numpy as np
from scipy.spatial import distance as dist
from collections import OrderedDict
import json


def get_transformed_points(box, perspective_transform):
    points = np.array([[[int(box[0] + (box[2] * 0.5)), int(box[1] + box[3])]]], dtype="float32")
    bd_pnt = cv2.perspectiveTransform(points, perspective_transform)[0][0]
    return int(bd_pnt[0]), int(bd_pnt[1])


class CentroidTracker:
    def __init__(self, settings_file):
        self.settings_file = settings_file
        self.roi_points = self.get_roi_from_settings()
        self.nextObjectID = 1
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.maxFramesDisappeared = 40
        self.objects_data = OrderedDict()

    def get_roi_from_settings(self):
        with open(self.settings_file, 'r') as settings:
            return json.load(settings)['roi_points']

    def register(self, centroid, box, frame_size):
        self.objects[self.nextObjectID] = centroid
        self.objects_data[self.nextObjectID] = centroid, box, self.calculate_person_cord(box, frame_size)
        self.disappeared[self.nextObjectID] = 0
        self.nextObjectID += 1

    def deregister(self, objectID):
        del self.objects[objectID]
        del self.disappeared[objectID]
        del self.objects_data[objectID]

    def update(self, inputCentroids, boxes, frame_size):
        if len(inputCentroids) == 0:
            for objectID in list(self.disappeared.keys()):
                self.disappeared[objectID] += 1

                if self.disappeared[objectID] > self.maxFramesDisappeared:
                    self.deregister(objectID)

            return self.objects

        if len(self.objects) == 0:
            for i in range(0, len(inputCentroids)):
                self.register(inputCentroids[i], boxes[i], frame_size)

        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = list(self.objects.values())
            D = dist.cdist(np.array(objectCentroids), inputCentroids)

            rows = D.min(axis=1).argsort()

            cols = D.argmin(axis=1)[rows]

            usedRows = set()
            usedCols = set()

            for (row, col) in zip(rows, cols):
                if row in usedRows or col in usedCols:
                    continue

                objectID = objectIDs[row]
                self.objects[objectID] = inputCentroids[col]
                self.objects_data[objectID] = inputCentroids[col], boxes[col], self.calculate_person_cord(boxes[col],
                                                                                                          frame_size)
                self.disappeared[objectID] = 0

                usedRows.add(row)
                usedCols.add(col)

            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)

            if D.shape[0] >= D.shape[1]:
                for row in unusedRows:
                    objectID = objectIDs[row]
                    self.disappeared[objectID] += 1
                    if self.disappeared[objectID] > self.maxFramesDisappeared:
                        self.deregister(objectID)

            else:
                for col in unusedCols:
                    self.register(inputCentroids[col], boxes[col], frame_size)
        return self.objects

    def calculate_person_cord(self, box, frame_size):
        (H, W) = frame_size
        src = np.float32(np.array(self.roi_points[:4]))
        dst = np.float32([[0, H], [W, H], [W, 0], [0, 0]])
        perspective_transform = cv2.getPerspectiveTransform(src, dst)
        return get_transformed_points(box, perspective_transform)
