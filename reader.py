import os
import json
from calculations.presence_time import PresenceTime
from calculations.average_speed_time import SpeedEstimator
from calculations.distance_estimation import DistanceEstimator
from calculations.minimal_distance import MinDistanceEstimator
from calculations.person_width import PersonWidthEstimator
from threading import Thread


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class DataReader(metaclass=SingletonMeta):

    def __init__(self, json_raw_file, settings):
        self.presence_time = PresenceTime(settings)
        self.avg_speed_time = SpeedEstimator(settings)
        self.distance_estimation = DistanceEstimator(settings)
        self.min_distance_estimation = MinDistanceEstimator(settings)
        self.person_avg_width_estimation = PersonWidthEstimator(settings)
        self.json_raw_file = json_raw_file
        self.settings = settings
        self.what_should_be_analyzed = self.check_characteristics_to_calculate()
        self.data = None
        self.last_modified_date = None
        self.load_data()
        self.is_running = True

    def check_characteristics_to_calculate(self):
        results_list = []
        for characteristic in self.settings['characteristics']:
            if characteristic == 'presence_time':
                results_list.append(self.presence_time)
            if characteristic == 'movement_speed':
                results_list.append(self.avg_speed_time)
            if characteristic == 'distance':
                results_list.append(self.distance_estimation)
            if characteristic == 'min_distance':
                results_list.append(self.min_distance_estimation)
            if characteristic == 'avg_person_width':
                results_list.append(self.person_avg_width_estimation)
        return results_list

    def load_data(self):
        if os.path.isfile(self.json_raw_file):
            with open(self.json_raw_file) as file:
                data = json.load(file)
                self.data = data
                self.last_modified_date = os.stat(self.json_raw_file).st_mtime
                self.run_calculations()

    def reload_data(self):
        while self.is_running:
            if os.path.isfile(self.json_raw_file):
                modified_date = os.stat(self.json_raw_file).st_mtime
                if modified_date != self.last_modified_date:
                    try:
                        with open(self.json_raw_file) as file:
                            self.data = json.load(file)
                        self.last_modified_date = modified_date
                        self.run_calculations()
                    except:
                        print('Skipping analysis')

    def run_calculations(self):
        threads = []
        for element in self.what_should_be_analyzed:
            threads.append(Thread(target=element.calculate, args=(self.data['data'], )))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
