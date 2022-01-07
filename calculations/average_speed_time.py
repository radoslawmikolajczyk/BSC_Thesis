from calculations.utils import Calculation, calculate_distance, get_frame_details
import os
import json
from collections import OrderedDict


class SpeedEstimator(Calculation):

    def __init__(self, settings):
        self.results_dir = settings['results_dir']
        self.roi, self.frame_width, self.frame_height = get_frame_details(settings)
        self.registered_person_speed = OrderedDict()

    def calculate(self, data):
        if self.roi is not None:
            for element in data:
                start_time = element['time']
                all_people = element['people']
                for person in all_people:
                    current_id = person['id']
                    if current_id in self.registered_person_speed.keys():
                        continue
                    current_position = person['person_pos']
                    for reversed_element in reversed(data):
                        end_time = reversed_element['time']
                        rev_people = reversed_element['people']
                        for last_person in rev_people:
                            if current_id == last_person['id'] and last_person['id'] \
                                    not in self.registered_person_speed.keys():
                                last_position = last_person['person_pos']
                                distance = calculate_distance(current_position, last_position, self.roi,
                                                              self.frame_height, self.frame_width)
                                try:
                                    speed = distance / (end_time - start_time)
                                except ZeroDivisionError:
                                    speed = 0
                                speed = speed * 0.036
                                if speed > 1.4:
                                    self.registered_person_speed[current_id] = speed
            if len(self.registered_person_speed) != 0:
                self.save_results()

    def save_results(self):
        if os.path.isdir(self.results_dir):
            if len(self.registered_person_speed) > 0:
                avg_speed = round(sum(self.registered_person_speed.values()) / len(self.registered_person_speed), 2)
            else:
                avg_speed = 0
            people = []
            for (person_id, speed) in self.registered_person_speed.items():
                people.append({"id": person_id, "avg_speed": speed})
            out = {"people": people, "avg_speed": avg_speed}
            file = self.results_dir + '/avg_speed.json'
            result = json.dumps(out)
            with open(file, 'w') as output:
                output.write(result)
            self.registered_person_speed = OrderedDict()
