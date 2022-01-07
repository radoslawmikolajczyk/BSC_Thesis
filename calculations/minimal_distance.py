from calculations.utils import Calculation, calculate_distance, get_frame_details
import os
import json
from collections import OrderedDict


class MinDistanceEstimator(Calculation):

    def __init__(self, settings):
        self.results_dir = settings['results_dir']
        self.roi, self.frame_width, self.frame_height = get_frame_details(settings)
        self.registered_distances = OrderedDict()

    def calculate(self, data):
        if self.roi is not None:
            for element in data:
                for person in element['people']:
                    current_id = person['id']
                    distances = OrderedDict()
                    for next_person in element['people']:
                        if next_person['id'] != current_id:
                            distance = calculate_distance(person['person_pos'], next_person['person_pos'], self.roi,
                                                          self.frame_height, self.frame_width)
                            distances[next_person['id']] = distance
                    if current_id not in self.registered_distances.keys():
                        self.registered_distances[current_id] = distances
                    else:
                        self.find_minimum(current_id, distances)
            if len(self.registered_distances) != 0:
                self.save_results()
                self.registered_distances = OrderedDict()

    def find_minimum(self, person_id, distances):
        registered_distances = self.registered_distances[person_id]
        for (pers_id, distance) in distances.items():
            if pers_id in registered_distances.keys():
                registered_distances[pers_id] = min(distance, registered_distances[pers_id])
            else:
                registered_distances[pers_id] = distance
        self.registered_distances[person_id] = registered_distances

    def save_results(self):
        if os.path.isdir(self.results_dir):
            people = []
            min_distance = float('inf')
            for person_id, distances in self.registered_distances.items():
                if not distances.values():
                    continue
                if min(list(distances.values())) < min_distance:
                    min_distance = min(list(distances.values()))
                person = {"id": person_id}
                dist = []
                for to_id, distance in distances.items():
                    dist.append({"to_id": to_id, "min_distance": distance})
                person["distances"] = dist
                people.append(person)
            out = {"people": people, "min_distance_from_all": min_distance}
            file = self.results_dir + '/min_distance.json'
            result = json.dumps(out)
            with open(file, 'w') as output:
                output.write(result)
