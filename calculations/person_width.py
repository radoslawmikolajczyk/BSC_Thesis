from calculations.utils import Calculation, calculate_distance, get_frame_details
import os
import json
from collections import OrderedDict
import numpy as np
import cv2


class PersonWidthEstimator(Calculation):

    def __init__(self, settings):
        self.results_dir = settings['results_dir']
        self.roi_for_people_width = settings['roi_for_person_width']
        self.roi, self.frame_width, self.frame_height = get_frame_details(settings)
        self.registered_width = OrderedDict()
        self.people_avg_width = OrderedDict()
        self.perspective = self.get_perspective()

    def calculate(self, data):
        if self.roi is not None and self.roi_for_people_width is not None:
            people = self.filter_data(data)
            for person in people:
                current_bbox = person['bbox']
                left_corner_coord = [current_bbox[0], current_bbox[1]]
                right_corner_coord = [current_bbox[0]+current_bbox[2], current_bbox[1]]
                transformed_points = self.transform_point(left_corner_coord, right_corner_coord)
                person_width = calculate_distance(transformed_points[0], transformed_points[1], self.roi,
                                                  self.frame_height, self.frame_width)
                if person['id'] not in self.registered_width.keys():
                    self.registered_width[person['id']] = [person_width/2]
                else:
                    self.registered_width[person['id']].append(person_width/2)
            for (person_id, widths) in self.registered_width.items():
                self.people_avg_width[person_id] = sum(widths) / len(widths)
            if len(self.people_avg_width) != 0:
                self.save_results()

    def filter_data(self, data):
        people = []
        for element in data:
            for person in element['people']:
                (x, y) = person['centroid_cord']
                if (self.roi_for_people_width[0][0] <= x <= self.roi_for_people_width[1][0]) and \
                        (self.roi_for_people_width[2][1] <= y <= self.roi_for_people_width[0][1]):
                    people.append(person)
        return people

    def get_perspective(self):
        (H, W) = self.frame_height, self.frame_width
        src = np.float32(np.array(self.roi[:4]))
        dst = np.float32([[0, H], [W, H], [W, 0], [0, 0]])
        return cv2.getPerspectiveTransform(src, dst)

    def transform_point(self, point_a, point_b):
        points_a = np.array([[[point_a[0], point_a[1]]]], dtype="float32")
        transformed_a = cv2.perspectiveTransform(points_a, self.perspective)[0][0]

        points_b = np.array([[[point_b[0], point_b[1]]]], dtype="float32")
        transformed_b = cv2.perspectiveTransform(points_b, self.perspective)[0][0]
        return transformed_a, transformed_b

    def save_results(self):
        if os.path.isdir(self.results_dir):
            avg_width = sum(list(self.people_avg_width.values())) / len(self.people_avg_width)
            people = []
            for (person_id, width) in self.people_avg_width.items():
                people.append({"id": person_id, "avg_person_width": width})
            out = {"people": people, "avg_width": avg_width}
            file = self.results_dir + '/avg_person_width.json'
            result = json.dumps(out, indent=1)
            with open(file, 'w') as output:
                output.write(result)
            self.people_avg_width = OrderedDict()
            self.registered_width = OrderedDict()
