from calculations.utils import Calculation
import json
from collections import OrderedDict


class PresenceTime(Calculation):

    def __init__(self, settings):
        self.results_dir = settings['results_dir']
        self.people_appeared_time = OrderedDict()
        self.people_presence_time = OrderedDict()

    def calculate(self, data):
        for element in data:
            current_time = element['time']
            people_ids = []
            for person in element['people']:
                people_ids.append(person['id'])
                if person['id'] not in self.people_appeared_time.keys():
                    self.people_appeared_time[person['id']] = current_time
            self.update_people_on_scene(people_ids, current_time)

        for person_id in people_ids:
            if person_id not in self.people_presence_time.keys():
                presence_time = round(current_time - self.people_appeared_time[person_id], 2)
                if presence_time > 0:
                    self.people_presence_time[person_id] = presence_time

        if len(self.people_presence_time) != 0:
            self.save_results()

    def update_people_on_scene(self, people_ids, current_time):
        registered_people = set(list(self.people_appeared_time.keys()))
        current_people = set(people_ids)
        diff = list(registered_people - current_people)
        if len(diff) != 0:
            for el in diff:
                self.people_presence_time[el] = round(current_time - self.people_appeared_time[el], 2)
                del self.people_appeared_time[el]

    def save_results(self):
        json_object = self.build_json()
        file_name = self.results_dir + '/presence_time.json'
        with open(file_name, "w") as outfile:
            outfile.write(json_object)
        self.people_presence_time = OrderedDict()
        self.people_appeared_time = OrderedDict()

    def build_json(self):
        json_data = {'people': []}
        for (personID, presence_time) in self.people_presence_time.items():
            json_data['people'].append({'id': personID, 'presence_time': presence_time})
        json_data['avg_time'] = self.count_avg_time()
        return json.dumps(json_data, indent=1)

    def count_avg_time(self):
        return round(sum(self.people_presence_time.values()) / len(self.people_presence_time), 2)
