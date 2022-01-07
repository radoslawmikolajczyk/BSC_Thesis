from tkinter import *
import threading
from processing import Analyzer
from tkinter import messagebox, filedialog
import core
import json
import os

global is_running


class App:

    def __init__(self, app_width=600, app_height=400):
        self.window = Tk()
        self.window.title('System aiding calibration and validation of models for pedestrian dynamics')
        self.window.iconphoto(True, PhotoImage(file='pedestrian.png'))
        self.app_width = app_width
        self.app_height = app_height
        self.settings_file = core.build_dir('settings') + '/settings.json'
        self.set_app_size()
        self.analyzer = None
        self.app_threads = []
        self.is_cancel = False

        self.first_screen = Frame(self.window)
        self.stream_input_var = StringVar()
        self.stream_input_var.trace('w', self.check_if_stream_not_blank)
        self.stream_label = Label(self.first_screen, text='Specify video input stream',
                                  font=('Helvetica', 12)).pack(pady=10)
        self.stream_input = Entry(self.first_screen, textvariable=self.stream_input_var, width=60).pack(pady=10)
        self.select_dir_label = Label(self.first_screen, text='Please select directory to save characteristics:',
                                      font=('Helvetica', 10)).pack(pady=10)
        self.browse_directory_button = Button(self.first_screen, text='Browse directory', command=self.browse_dir,
                                              font=('Helvetica', 10))
        self.browse_directory_button.pack(pady=10)
        self.selected_directory_var = StringVar()
        self.selected_directory_var.trace('w', self.check_if_stream_not_blank)
        self.destination_dir_label = Label(self.first_screen, textvariable=self.selected_directory_var,
                                           font=('Helvetica', 10)).pack(pady=10)
        self.goto_second_frame_button = Button(self.first_screen, text='Next',
                                               command=self.setup_second_frame,
                                               font=('Helvetica', 10))
        self.goto_second_frame_button.config(state='disabled')
        self.goto_second_frame_button.pack(pady=20)
        self.first_screen.pack()

        self.second_screen = Frame(self.window)
        self.frame_amount_var = StringVar(value='All')
        self.analyze_time_label = Label(self.second_screen, text='Specify the number of frames to be analyzed',
                                        font=('Helvetica', 12)).pack(pady=10)
        self.infinite_button = Radiobutton(self.second_screen, text='Infinite (Till video stream will terminate)',
                                           variable=self.frame_amount_var, value='All', font=('Helvetica', 10),
                                           command=self.check_frame_amount)
        self.infinite_button.pack(anchor=W)
        self.specified_frame_num_button = Radiobutton(self.second_screen, text='Specified',
                                                      variable=self.frame_amount_var, value='Specified',
                                                      font=('Helvetica', 10), command=self.check_frame_amount)
        self.specified_frame_num_button.pack(anchor=W)
        self.specified_frames_label = Label(self.second_screen, text='Put the number of frames:',
                                            font=('Helvetica', 10))
        self.specified_frames_var = StringVar()
        self.specified_frame_input = Entry(self.second_screen, textvariable=self.specified_frames_var, width=30)

        self.goto_third_frame_button = Button(self.second_screen, text='Next',
                                              command=self.setup_third_frame,
                                              font=('Helvetica', 10))
        self.goto_third_frame_button.pack(in_=self.second_screen, side=RIGHT, pady=20)
        self.back_to_first_frame_button = Button(self.second_screen, text='Back', command=self.setup_first_frame,
                                                 font=('Helvetica', 10))
        self.back_to_first_frame_button.pack(in_=self.second_screen, side=LEFT, pady=20)

        self.third_screen = Frame(self.window)
        self.pick_options_label = Label(self.third_screen, text='Select the characteristics to be calculated',
                                        font=('Helvetica', 12)).pack(pady=10)
        self.presence_time_var = IntVar()
        self.presence_time_checkbox = Checkbutton(self.third_screen,
                                                  text='Calculate presence time for each person on the scene',
                                                  font=('Helvetica', 10), variable=self.presence_time_var,
                                                  onvalue=1, offvalue=0)
        self.presence_time_checkbox.pack(anchor="w")
        self.movement_speed_var = IntVar()
        self.movement_speed_checkbox = Checkbutton(self.third_screen,
                                                   text='Calculate movement speed for each person on the scene',
                                                   font=('Helvetica', 10), variable=self.movement_speed_var,
                                                   onvalue=1, offvalue=0)
        self.movement_speed_checkbox.pack(anchor="w")
        self.distance_var = IntVar()
        self.distance_checkbox = Checkbutton(self.third_screen,
                                             text='Calculate distance between people (every 25 frames)',
                                             font=('Helvetica', 10), variable=self.distance_var, onvalue=1, offvalue=0)
        self.distance_checkbox.pack(anchor="w")
        self.min_distance_var = IntVar()
        self.min_distance_checkbox = Checkbutton(self.third_screen, text='Calculate minimal distance between people',
                                                 font=('Helvetica', 10), variable=self.min_distance_var,
                                                 onvalue=1, offvalue=0)
        self.min_distance_checkbox.pack(anchor="w")
        self.person_avg_width_var = IntVar()
        self.person_avg_width_checkbox = Checkbutton(self.third_screen, onvalue=1, offvalue=0,
                                                     text='Calculate the average width of a person\'s shoulders',
                                                     font=('Helvetica', 10), variable=self.person_avg_width_var)
        self.person_avg_width_checkbox.pack(anchor="w")

        self.goto_fourth_screen_button = Button(self.third_screen, text='Next', command=self.setup_fourth_frame,
                                                font=('Helvetica', 10))
        self.goto_fourth_screen_button.pack(in_=self.third_screen, side=RIGHT, pady=20)
        self.back_to_second_frame_button = Button(self.third_screen, text='Back', command=self.setup_second_frame,
                                                  font=('Helvetica', 10))
        self.back_to_second_frame_button.pack(in_=self.third_screen, side=LEFT, pady=20)

        self.fourth_screen = Frame(self.window)
        self.summary_label = Label(self.fourth_screen, text='Settings summary and analyzing',
                                   font=('Helvetica', 12)).pack(pady=10)

        self.summary_stream_label = Label(self.fourth_screen, text='Video stream:',
                                          font=('Helvetica', 10, 'bold')).pack(anchor=CENTER)
        self.summary_stream = Label(self.fourth_screen, textvariable=self.stream_input_var,
                                    font=('Helvetica', 8)).pack(anchor=CENTER)
        self.summary_directory_label = Label(self.fourth_screen, text='Output directory:',
                                             font=('Helvetica', 10, 'bold')).pack(anchor=CENTER)
        self.summary_directory = Label(self.fourth_screen, textvariable=self.selected_directory_var,
                                       font=('Helvetica', 8)).pack(anchor=CENTER)
        self.frames_label = Label(self.fourth_screen, text='Frames:',
                                  font=('Helvetica', 10, 'bold')).pack(anchor=CENTER)
        self.frames = Label(self.fourth_screen, textvariable=self.specified_frames_var,
                            font=('Helvetica', 8)).pack(anchor=CENTER)

        self.start_analyzing_button = Button(self.fourth_screen, text='Start analyzing', command=self.start_analyzing,
                                             font=('Helvetica', 10))
        self.start_analyzing_button.pack(pady=10)

        self.stop_analyzing_button = Button(self.fourth_screen, text='Stop analyzing', command=self.stop_analyzing,
                                            font=('Helvetica', 10))
        self.stop_analyzing_button['state'] = 'disabled'
        self.stop_analyzing_button.pack()

        self.progress_var = StringVar()
        self.progress_label = Label(self.fourth_screen, text='Progress:',
                                    font=('Helvetica', 10))
        self.progress_label.pack(pady=10)
        self.progress = Label(self.fourth_screen, textvariable=self.progress_var, font=('Helvetica', 10))
        self.progress.pack()
        self.back_to_third_frame_button = Button(self.fourth_screen, text='Back', command=self.back_to_third_frame,
                                                 font=('Helvetica', 10))
        self.back_to_third_frame_button.pack(pady=20)

        self.load_settings()

    def set_app_size(self):
        self.window.resizable(0, 0)

        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        position_x = (screen_width / 2) - (self.app_width / 2)
        position_y = (screen_height / 2) - (self.app_height / 2)

        self.window.geometry('%dx%d+%d+%d' % (self.app_width, self.app_height, position_x, position_y))

    def run(self):
        self.window.protocol("WM_DELETE_WINDOW", self.close_app)
        self.window.mainloop()

    def close_app(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.is_cancel = True
            if self.analyzer is not None:
                self.stop_analyzing()
            self.window.destroy()

    def setup_first_frame(self):
        self.second_screen.pack_forget()
        self.first_screen.pack()
        self.save_settings()

    def check_if_stream_not_blank(self, *args):
        if self.stream_input_var.get() != '' and self.selected_directory_var.get() != '':
            self.goto_second_frame_button['state'] = 'active'

    def setup_second_frame(self):
        self.first_screen.pack_forget()
        self.third_screen.pack_forget()
        self.second_screen.pack()
        self.save_settings()

    def check_frame_amount(self):
        if self.frame_amount_var.get() == 'Specified':
            self.specified_frames_label.pack(pady=10)
            self.specified_frame_input.pack()
            self.goto_third_frame_button.pack_configure(pady=80)
        else:
            self.specified_frames_label.pack_forget()
            self.specified_frame_input.pack_forget()
            self.goto_third_frame_button.pack_configure(pady=20)

    def setup_third_frame(self):
        if self.frame_amount_var.get() == 'Specified':
            try:
                int(self.specified_frame_input.get())
                self.specified_frames_var.set(self.specified_frame_input.get())
                self.second_screen.pack_forget()
                self.third_screen.pack()
            except ValueError:
                messagebox.showinfo("Incorrect input type!", "Number of frames must be integer!")
        else:
            self.specified_frames_var.set('All')
            self.second_screen.pack_forget()
            self.third_screen.pack()
        self.save_settings()

    def browse_dir(self):
        filename = filedialog.askdirectory()
        self.selected_directory_var.set(filename)

    def setup_fourth_frame(self):
        self.third_screen.pack_forget()
        self.fourth_screen.pack()
        self.save_settings()

    def back_to_third_frame(self):
        self.fourth_screen.pack_forget()
        self.third_screen.pack()

    def start_analyzing(self):
        global is_running
        is_running = True
        self.analyzer = Analyzer()
        self.app_threads.append(threading.Thread(target=self.analyzer.run_processing))
        self.app_threads.append(threading.Thread(target=self.update_progress))
        for thread in self.app_threads:
            thread.start()
        self.start_analyzing_button['state'] = 'disabled'
        self.stop_analyzing_button['state'] = 'active'
        self.back_to_third_frame_button['state'] = 'disabled'

    def update_progress(self):
        global is_running
        while is_running:
            if self.specified_frames_var.get() == 'All':
                self.progress_var.set('Frames analyzed: ' + str(core.analyzed_frame))
            else:
                percent = str(round((core.analyzed_frame / int(self.specified_frames_var.get())) * 100, 2))
                self.progress_var.set('Percent of done: ' + percent + ' %')

    def stop_analyzing(self):
        if not self.is_cancel:
            messagebox.showinfo("INFO", "Analysis is stopped, if you want to analyze again, rerun the system")
        global is_running
        is_running = False
        self.analyzer.stop_processing()
        self.app_threads = []

    def load_settings(self):
        if os.path.isfile(self.settings_file):
            with open(self.settings_file) as file:
                try:
                    data = json.load(file)
                except:
                    return
            if len(data) == 0:
                return
            if data['video_stream'] != '':
                self.stream_input_var.set(data['video_stream'])
            if data['results_dir'] != '':
                self.selected_directory_var.set(data['results_dir'])
            if data['frames_to_analyze'] != '':
                if data['frames_to_analyze'] != 'All' and type(data['frames_to_analyze']) is int:
                    self.frame_amount_var.set('Specified')
                    self.check_frame_amount()
                    self.specified_frames_var.set(data['frames_to_analyze'])
            if data['characteristics']:
                for element in data['characteristics']:
                    if element == 'presence_time':
                        self.presence_time_var.set(1)
                    if element == 'movement_speed':
                        self.movement_speed_var.set(1)
                    if element == 'distance':
                        self.distance_var.set(1)
                    if element == 'min_distance':
                        self.min_distance_var.set(1)
                    if element == 'avg_person_width':
                        self.person_avg_width_var.set(1)

    def save_settings(self):
        settings_file = open(self.settings_file, 'r')
        try:
            data = json.load(settings_file)
        except:
            data = {'video_stream': self.stream_input_var.get(),
                    'results_dir': self.selected_directory_var.get()}
        settings_file.close()
        data['video_stream'] = self.stream_input_var.get()
        data['results_dir'] = self.selected_directory_var.get()
        if self.frame_amount_var.get() == 'All':
            data['frames_to_analyze'] = 'All'
        else:
            try:
                data['frames_to_analyze'] = int(self.specified_frames_var.get())
            except Exception:
                print('Attempt to save wrong frames format!')
        characteristics = []
        if self.presence_time_var.get() == 1:
            characteristics.append('presence_time')
        if self.movement_speed_var.get() == 1:
            characteristics.append('movement_speed')
        if self.distance_var.get() == 1:
            characteristics.append('distance')
        if self.min_distance_var.get() == 1:
            characteristics.append('min_distance')
        if self.person_avg_width_var.get() == 1:
            characteristics.append('avg_person_width')
        data['characteristics'] = characteristics

        with open(self.settings_file, 'w') as outfile:
            json.dump(data, outfile, indent=1)
