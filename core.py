import numpy as np
import cv2
from tracker import CentroidTracker
import json
from collections import OrderedDict
import os


class YoloConfig:

    def __init__(self, blob_image_size=(608, 608), saving_frames_seq=10):
        self.cfg = build_dir('yolo_models/yolov4.cfg')
        self.weights = build_dir('yolo_models/yolov4.weights')
        self.coco_names = build_dir('yolo_models/coco.names')
        self.blob_image_size = blob_image_size
        self.saving_frames_seq = saving_frames_seq


def build_dir(suffix):
    return os.getcwd().replace('\\', '/').__add__('/{}'.format(suffix))


global analyzed_frame


class Core:

    def __init__(self, yolo_config: YoloConfig, stream, save_directory, save_frames=0):
        self.yolo_config = yolo_config
        self.stream = stream
        self.tracker = CentroidTracker(build_dir('settings') + '/settings.json')
        self.confidence = 0.4
        self.threshold = 0.1
        self.current_frame = 1
        self._json_data = OrderedDict()
        self.save_directory = save_directory
        self.stop_analyzing_flag = False
        self.save_frames = save_frames

    def set_confidence(self, confidence):
        self.confidence = confidence

    def set_threshold(self, threshold):
        self.threshold = threshold

    def start_processing(self, infinite=True, frames=100):
        global analyzed_frame
        analyzed_frame = 0
        darknet = cv2.dnn.readNetFromDarknet(self.yolo_config.cfg, self.yolo_config.weights)
        if cv2.cuda.getCudaEnabledDeviceCount() != 0:
            darknet.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
            darknet.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
        layer_names = darknet.getLayerNames()
        layer_names = [layer_names[i[0] - 1] for i in darknet.getUnconnectedOutLayers()]
        coco_labels = open(self.yolo_config.coco_names).read().strip().split("\n")
        capture_video = cv2.VideoCapture(self.stream)
        self._json_data['data'] = []
        calibration_data = np.load(build_dir('settings') + '/calibration.npz')
        if self.save_frames > 0:
            if not os.path.isdir(self.save_directory+'/frames'):
                os.mkdir(self.save_directory+'/frames')
        isNewMatrixCalculated = False
        while (infinite or frames > 0) and not self.stop_analyzing_flag:
            ret, frame = capture_video.read()

            if not ret:
                break

            h, w = frame.shape[:2]
            if not isNewMatrixCalculated:
                new_camera_mtx, roi = cv2.getOptimalNewCameraMatrix(calibration_data['matrix'],
                                                                    calibration_data['distortion'], (w, h), 0, (w, h))
                isNewMatrixCalculated = True

            dst = cv2.undistort(frame, calibration_data['matrix'], calibration_data['distortion'], None, new_camera_mtx)
            x, y, w, h = roi
            frame = dst[y:y + h, x:x + w]

            raw_frame = frame.copy()
            (H, W) = frame.shape[:2]

            blob = cv2.dnn.blobFromImage(frame, 1 / 255.0,
                                         (self.yolo_config.blob_image_size[0], self.yolo_config.blob_image_size[1]),
                                         swapRB=True, crop=False)
            darknet.setInput(blob)
            layerOutputs = darknet.forward(layer_names)

            boxes = []
            confidences = []
            centroids = []
            NMS_boxes = []

            for output in layerOutputs:
                for detection in output:
                    scores = detection[5:]
                    classID = np.argmax(scores)
                    confidence = scores[classID]
                    if confidence > self.confidence and coco_labels[classID] == 'person':
                        box = detection[0:4] * np.array([W, H, W, H])
                        (centerX, centerY, width, height) = box.astype("int")
                        x = int(centerX - (width / 2))
                        y = int(centerY - (height / 2))
                        boxes.append([x, y, int(width), int(height)])
                        confidences.append(float(confidence))
            indexes = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence, self.threshold)

            if len(indexes) > 0:
                for i in indexes.flatten():
                    (x, y) = (boxes[i][0], boxes[i][1])
                    (w, h) = (boxes[i][2], boxes[i][3])
                    NMS_boxes.append((x, y, w, h))
                    centroids.append((boxes[i][0] + boxes[i][2] / 2, boxes[i][1] + boxes[i][3] / 2))
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

            objects = self.tracker.update(centroids, NMS_boxes, frame_size=(H, W))

            for (objectID, centroid) in objects.items():
                text = "ID {}".format(objectID)
                cv2.putText(frame, text, (int(centroid[0]) - 10, int(centroid[1]) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.circle(frame, (int(centroid[0]), int(centroid[1])), 3, (0, 255, 0), -1)

            people = []
            for (objectID, values) in self.tracker.objects_data.items():
                people.append({'id': objectID, 'bbox': values[1], 'centroid_cord': values[0], 'person_pos': values[2]})

            if self.current_frame == 1:
                seconds = 0.00
            else:
                seconds = round(self.current_frame / capture_video.get(cv2.CAP_PROP_FPS), 2)
            self._json_data['data'].append({'frame': self.current_frame, 'time': seconds, 'people': people})
            print('Analyzed frame: ', self.current_frame)
            if self.current_frame % self.save_frames == 0:
                cv2.imwrite(self.save_directory+'/frames/Frame{}.jpg'.format(self.current_frame), frame)

            self.current_frame += 1
            analyzed_frame += 1
            frames -= 1

            if frames % self.yolo_config.saving_frames_seq == 0:
                self.build_json_output(self._json_data)

        capture_video.release()

    def build_json_output(self, data):
        json_object = json.dumps(data)
        file_name = self.save_directory + '/raw_data.json'
        with open(file_name, "w") as outfile:
            outfile.write(json_object)
