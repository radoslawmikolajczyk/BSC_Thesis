import distutils
import os
import platform
from distutils import util
from App import App
import argparse
import sys
import wget
from processing import Analyzer

parser = argparse.ArgumentParser(description='System aiding calibration and validation of models for pedestrian '
                                             'dynamics')
parser.add_argument('--run_gui', metavar='run_gui', type=str, help='Boolean to run gui or not', required=True)

args = parser.parse_args()
run_gui = args.run_gui

try:
    run_gui = bool(distutils.util.strtobool(run_gui))
except:
    print('Incorrect --run_gui type! Type True or False')
    sys.exit()

try:
    if not os.path.exists('yolo_models/yolov4.weights'):
        os_name = platform.system()
        output_dir = 'yolo_models'
        url = 'https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v3_optimal/yolov4.weights'
        print('Downloading YOLOv4 model...')
        if os_name == 'Windows':
            filename = wget.download(url, out=output_dir)
        else:
            print('Download YOLOv4 model and paste it to yolo_models folder. Url: '
                  'https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v3_optimal/yolov4.weights')
            sys.exit()
except:
    print('Exception occurred during downloading Yolo model!')

if __name__ == '__main__':
    if run_gui:
        App().run()
    else:
        analyzer = Analyzer()
        analyzer.run_processing()