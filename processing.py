from core import YoloConfig, Core
from threading import Thread
from reader import DataReader
import os
import sys
import json


class Analyzer:

    def __init__(self):
        self.settings_file = os.getcwd().replace('\\', '/') + '/settings/settings.json'
        self.settings = self.read_settings()
        self.yolo_config = YoloConfig()
        self.core_analyzer = Core(self.yolo_config, self.settings['video_stream'], self.settings['results_dir'],
                                  self.settings['save_frames_every'])
        self.raw_data = self.settings['results_dir'] + '/raw_data.json'
        self.reader = DataReader(self.raw_data, self.settings)

    def read_settings(self):
        if os.path.isfile(self.settings_file):
            with open(self.settings_file, 'r') as file:
                return json.load(file)
        else:
            sys.exit('Error: ./settings/settings.json file does not exist!')

    def run_processing(self):
        self.run_core()

    def run_core(self):
        if self.settings['frames_to_analyze'] != 'All':
            core_process = Thread(target=self.core_analyzer.start_processing,
                                  args=(False, self.settings['frames_to_analyze'],))
        else:
            core_process = Thread(target=self.core_analyzer.start_processing)
        threads = [core_process, Thread(target=self.reader.reload_data)]
        for t in threads:
            t.start()

    def stop_processing(self):
        self.core_analyzer.stop_analyzing_flag = True
        self.reader.is_running = False
