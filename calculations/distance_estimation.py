from calculations.utils import Calculation, calculate_distance, get_frame_details
import os
import json


class DistanceEstimator(Calculation):

    def __init__(self, settings):
        self.results_dir = settings['results_dir']
        self.roi, self.frame_width, self.frame_height = get_frame_details(settings)
        self.average_distance = []
        self.data = []

    def calculate(self, data):
        if self.roi is not None:
            for element in data:
                current_frame = element['frame']
                if current_frame % 25 != 0:
                    continue
                people = []
                for i in range(len(element['people'])):
                    current_id = element['people'][i]['id']
                    distances = []
                    for j in range(len(element['people'])):
                        if element['people'][i]['id'] != element['people'][j]['id']:
                            distance = calculate_distance(element['people'][i]['person_pos'],
                                                          element['people'][j]['person_pos'], self.roi,
                                                          self.frame_height, self.frame_width)
                            distances.append({"to_id": element['people'][j]['id'], "distance": distance})
                            self.average_distance.append(distance)
                    people.append({"id": current_id, "distances": distances})
                self.data.append({"frame": current_frame, "people": [people]})
            if len(self.average_distance) != 0:
                self.save_results()
        self.average_distance = []
        self.data = []

    def save_results(self):
        if os.path.isdir(self.results_dir):
            distance_sum = sum(self.average_distance)
            avg_distance = distance_sum / len(self.average_distance)
            out = {"data": self.data, "avg_distance": avg_distance}
            file = self.results_dir + '/distance.json'
            result = json.dumps(out)
            with open(file, 'w') as output:
                output.write(result)
