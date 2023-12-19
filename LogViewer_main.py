# import tkinter
# from tkinter import filedialog
import os
import sys
import time

import struct
import numpy as np
import pandas as pd
#from matplotlib import pyplot as plt
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import pickle
import copy
import math


from PIL import Image


from PySide6.QtWidgets import *
# ref: https://www.pythonguis.com/faq/pyqt6-vs-pyside6/
from PySide6.QtCore import Signal, Slot # PySide6: Signal, Slot, PyQt6: pyqtSignal, pyqtSlot
from PySide6.QtCore import QTimer, Qt, QDir


import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import pyqtgraph as pg

from threading import Lock, Thread


import datetime
import Utils
import LogReader
import LogReporter



g_entire_data = [0,0]
g_data_lock = Lock()

G_DEFAULT_FILE_PATH = r'E:\22_AVP_LOG\AVP_LOG_oci\2023_11\VT41-ID02\vt41-id02-2023_11_07'
G_DEFAULT_FOLDER_PATH = r"E:\22_AVP_LOG\AVP_LOG_dmz-20231103"


class PGCanvase(QWidget):
    def __init__(self):
        super().__init__()

        self.canvas = pg.PlotWidget(title="Relative D-V Graphe")
        self.canvas.plotItem.setLabels(bottom='Relative Distance', left='Relative Velocity')
        self.canvas.setBackground('w')

# # 1) 4.1 세상에 더 빠른 방법이 - pyqtgraph
# # ref: https://dnai-deny.tistory.com/67?category=1361770
# # 2) 태양광 모니터링 시스템 - pyqtgraph <-- 이게 나한테는 더 필요한듯
# # ref: https://fantasy297.tistory.com/641
# class PGCanvasWButton(QWidget):
#     def __init__(self):
#         super().__init__()

#         self.graph_data = []
#         self.label_main = QLabel("PyQTGraph Canvase")

#         self.canvas = pg.PlotWidget(title="Relative D-V Graphe")
#         self.canvas.plotItem.setLabels(bottom='Relative Distance', left='Relative Velocity')
#         self.canvas.setBackground('w')

#         # timer를 생성하고, timeout이 되면 get_data를 호출함
#         # timer자체를 start/stop할 수 있음
#         self.qTimer = QTimer()
#         self.qTimer.start(25)
#         self.qTimer.timeout.connect(self.get_data)

#         self.paused = False

#         # button 'Pause/Restart'
#         self.btn_pause = QPushButton(text="Pause/Restart")
#         self.btn_pause.clicked.connect(self.btn_clicked_pause)

#         # button 'Analysis'
#         self.btn_analysis = QPushButton(text="Analysis")
#         self.btn_analysis.clicked.connect(self.btn_clicked_analysis)

#         # button 'Calculate Distance'
#         self.btn_cal_dist = QPushButton(text="Calculate Distance")
#         self.btn_cal_dist.clicked.connect(self.btn_clicked_cal_dist)

#         layout_btns = QHBoxLayout()
#         layout_btns.addWidget(self.btn_pause)
#         layout_btns.addWidget(self.btn_analysis)
#         layout_btns.addWidget(self.btn_cal_dist)

#         box = QVBoxLayout()
#         box.addWidget(self.label_main)
#         box.addWidget(self.canvas)
#         box.addLayout(layout_btns)
#         box.setSpacing(30)
#         box.setContentsMargins(50, 50, 50, 50)
        
#         self.setLayout(box)

#         self.setGeometry(800, 300, 1500, 1000)
#         self.setWindowTitle("Relative Distance-Velocity Graphe")

#         self.canvas_p = self.canvas.plot(pen='b')

#         self.draw_chart()
#         self.show()

#     def btn_clicked_pause(self):
#         self.toggle_event()
            
#     def btn_clicked_cal_dist(self):
#         None

#     def toggle_event(self):
#         # Control animation. Pause/Restart
#         if self.paused:
#             self.qTimer.start()
#         else:
#             self.qTimer.stop()
#         self.paused = not self.paused

#     def draw_chart(self):
#         """
#         Update plot data
#         """
#         self.canvas_p.setData(self.graph_data)

#     @Slot()
#     def get_data(self):
#         """
#         Separating plotting data from entire data.
#         """
#         g_data_lock.acquire()
#         # if len(g_entire_data) > 100:
#         #     self.graph_data = g_entire_data[len(g_entire_data) - 100:]
#         # else:
#         #     self.graph_data = g_entire_data

#         self.graph_data.append(np.random.rand())

#         g_data_lock.release()
#         self.draw_chart()

##############################
# file select window
##############################
class W_FileSelect(QDialog):
    def __init__(self):
        super().__init__()

        total_layout = QVBoxLayout()

        self.setLayout(total_layout)    # 전체 layout 설정

        # l_layout = QVBoxLayout()
        # r_layout = QVBoxLayout()

        # layout.addLayout(l_layout)
        # layout.addLayout(r_layout)

        # label 'File to process'
        self.label_sel_file = QLabel('File to process', self)
        font_dir = self.label_sel_file.font()
        font_dir.setPointSize(12)
        font_dir.setFamily('Times New Roman')
        font_dir.setBold(True)
        self.label_sel_file.setFont(font_dir)

        # button 'Select log file'
        self.btn_select_file= QPushButton(text="Select log file")
        self.btn_select_file.clicked.connect(self.btn_clicked_select)

        # button 'Start Processing'
        self.btn_proc = QPushButton(text="Load data")
        self.btn_proc.clicked.connect(self.btn_clicked_load)

        # button 'Convert to CSV'
        self.btn_convert_to_csv = QPushButton(text="Convert to csv")
        self.btn_convert_to_csv.clicked.connect(self.btn_clicked_convert_to_csv)

        # button 'ACC simulation window'
        self.btn_sim = QPushButton(text="ACC simulation")
        self.btn_sim.clicked.connect(self.btn_clicked_sim)

        ly_btns = QHBoxLayout()
        ly_btns.addWidget(self.btn_select_file)
        ly_btns.addWidget(self.btn_proc)
        ly_btns.addWidget(self.btn_convert_to_csv)
        ly_btns.addWidget(self.btn_sim)

        #self.createControls()

        ly_file_sel = QGridLayout()

        # plain text edit
        self.edit_sel_file = QTextEdit()
        # fname, onoff, sidx, len
        # fname = r"E:/22_AVP_LOG/AVP_LOG_distance/2023_09/VT50-ID51/vt50-id51-2023_09_05/14h_10m_14s-X37.238739-Y126.772846.idx, 1, 0, 0"
        fname = QDir.toNativeSeparators(\
            r"E:\22_AVP_LOG\AVP_LOG_distance\AVP_LOG_oci_tmp\vt50-id51-2023_09_05\17h_07m_34s-X37.245085-Y126.775178.idx, 1, 0, 0")
        self.edit_sel_file.setPlainText(fname)

        ly_file_sel.addWidget(self.edit_sel_file, 0, 0)
        ly_file_sel.addWidget(self.createControlGroup(), 0, 1)


        self.btn_close_ok = QPushButton(text="Load data")
        # btnDialog.move(100, 100)
        self.btn_close_ok.clicked.connect(self.btn_clicked_close_ok)

        self.btn_close_cancel = QPushButton(text="Cancel")
        # btnDialog.move(100, 100)
        self.btn_close_cancel.clicked.connect(self.btn_clicked_close_cancel)        
        ly_btns_close = QHBoxLayout()  
        ly_btns_close.addWidget(self.btn_close_ok)
        ly_btns_close.addWidget(self.btn_close_cancel)      


        total_layout.addWidget(self.label_sel_file)
        total_layout.addLayout(ly_btns)
        total_layout.addLayout(ly_file_sel)
        total_layout.addLayout(ly_btns_close)

        self.label_status = QLabel("STATUS")
        # self.label_status.setStyleSheet("border: 1px solid black;") 

        total_layout.addWidget(self.label_status)

        # ly_sel_file = QVBoxLayout()
        # ly_sel_file.addWidget(self.label_sel_file)

        # ly_btns = QHBoxLayout()
        # ly_btns.addWidget(self.btn_select_file)
        # ly_btns.addWidget(self.btn_proc)
        # ly_btns.addWidget(self.btn_convert_to_csv)
        # ly_btns.addWidget(self.btn_sim)
        # cont_1 = QWidget()
        # cont_1.setLayout(ly_btns)
        # ly_sel_file.addWidget(cont_1)
        # ly_sel_file.addWidget(self.edit_sel_file)

        # self.total_layout.addLayout(ly_sel_file)


        ##########################
        # data frame
        self.full_df = None

        # for distance calculation
        self.vinfo_day_idx = []
        self.vinfo_day_t= []
        self.vinfo_day_dfs = []


    def createControlGroup(self):
        groupbox = QGroupBox('Group box')

        ly_grid = QGridLayout()

        chkbox1 = QCheckBox('Chk 1')
        chkbox2 = QCheckBox('Chk 2')
        chkbox3 = QCheckBox('Chk 3')

        n_spin = 3
        self.min_spinbox = []
        self.max_spinbox = []
        self.min_value = []
        for i in range(n_spin):
            spinbox_min = QSpinBox()
            spinbox_min.setMaximum(20000)
            spinbox_max = QSpinBox()
            spinbox_max.setMaximum(20000)

            self.min_spinbox.append(spinbox_min)
            self.max_spinbox.append(spinbox_max)

        # for i in range(n_spin):
        #     print("i:", i)
        #     self.min_spinbox[i].valueChanged.connect(lambda: self.value_changed(i, self.min_spinbox[i]))
        #     time.sleep(1)

        self.min_spinbox[0].valueChanged.connect(lambda: self.value_changed(0, self.min_spinbox[0]))
        self.min_spinbox[1].valueChanged.connect(lambda: self.value_changed(1, self.min_spinbox[1]))
        self.min_spinbox[2].valueChanged.connect(lambda: self.value_changed(2, self.min_spinbox[2]))

        ly_grid.addWidget(QLabel("ON"), 0, 0)
        ly_grid.addWidget(chkbox1, 1, 0)
        ly_grid.addWidget(chkbox2, 2, 0)
        ly_grid.addWidget(chkbox3, 3, 0)

        ly_grid.addWidget(QLabel("Min"), 0, 1)
        ly_grid.addWidget(self.min_spinbox[0], 1, 1)
        ly_grid.addWidget(self.min_spinbox[1], 2, 1)
        ly_grid.addWidget(self.min_spinbox[2], 3, 1)

        ly_grid.addWidget(QLabel("Max"), 0, 2)
        ly_grid.addWidget(self.max_spinbox[0], 1, 2)
        ly_grid.addWidget(self.max_spinbox[1], 2, 2)
        ly_grid.addWidget(self.max_spinbox[2], 3, 2)


        # vbox = QVBoxLayout()
        # vbox.addWidget(chkbox1)
        # vbox.addWidget(chkbox2)
        # vbox.addWidget(chkbox3)
        # vbox.addStretch(1)

        groupbox.setLayout(ly_grid)

        return groupbox

    def value_changed(self, idx, spinbox):
        print(self.min_spinbox[idx].value(), "idx:", idx)
        print(spinbox.value(), "spinbox:", id(spinbox))


    def btn_clicked_select(self):
        # QFileDialog information
        # https://newbie-developer.tistory.com/122
        # dir = QDir.toNativeSeparators(r"E:\22_AVP_LOG\AVP_LOG_oci")
        dir = QDir.toNativeSeparators(G_DEFAULT_FILE_PATH)
        filter = "Index Files (*.idx);;Text Files (*.txt);;All Files (*)"
        fnames, _ = QFileDialog.getOpenFileNames(self, "Select files", dir, filter)
        print(fnames)
        edit_names = ""
        for fname in fnames:
            # fname, onoff, sidx, len
            edit_names += QDir.toNativeSeparators(fname) + ", 1, 0, 0\n"
        self.edit_sel_file.setPlainText(edit_names)

    def btn_clicked_load(self):
        edit_text = self.edit_sel_file.toPlainText()

        fnames = edit_text.split('\n')
        print("fnames:", fnames)

        self.full_df = []   # init
        dfs = []
        n_files = len(fnames)
        for i, fname in enumerate(fnames):
            try:
                f_full, onoff_s, sidx_s, idx_len_s = fname.split(',')
            except Exception as e:
                print("Filename.split error, skip... - ", fname)
                continue

            onoff = int(onoff_s)
            sidx = int(sidx_s)
            idx_len = int(idx_len_s)
            if onoff == 0:
                print('OFF file: %s, skip...' % (f_full))
                continue

            getFullLog = 1

            processed_f_name, t_logs, df, info_curr = LogReader.read_one_file(f_full, getFullLog, sidx, idx_len)
            print("df:", df.shape, processed_f_name)
            dfs.append(df)  # full_df

            # append data for each day
            if info_curr in self.vinfo_day_idx:
                idx = self.vinfo_day_idx.index(info_curr)
                df_prev = self.vinfo_day_dfs[idx]
                t_prev = self.vinfo_day_t[idx]
                #print(len(t_prev), df_prev.shape)
                
                # ignore_index 가 없으면 다시 0부터 시작함
                self.vinfo_day_dfs[idx] = pd.concat([df_prev, df], ignore_index=True)
                self.vinfo_day_t[idx].extend(t_logs)
                #print(len(vinfo_day_t), vinfo_day_dfs[idx].shape)

                #plt.figure(str(vinfo_day_idx[idx]))
                #plt.plot(vinfo_day_t[idx])
                #plt.show()

            else:
                self.vinfo_day_idx.append(info_curr)
                self.vinfo_day_t.append(t_logs)
                self.vinfo_day_dfs.append(df)


            self.label_status.setText("(%d/%d):%s" % (i, n_files, processed_f_name))
            self.label_status.repaint()


        self.full_df = pd.concat(dfs, ignore_index=True)
        print('full_df:', self.full_df.shape)

    def btn_clicked_convert_to_csv(self):
        edit_text = self.edit_sel_file.toPlainText()

        fnames = edit_text.split('\n')
        print("fnames:", fnames)

        # convert df to 1st filename.csv
        f_full, onoff_s, sidx_s, idx_len_s = fnames[0].split(',')
        f = os.path.splitext(f_full)
        
        fname_csv = f[0] + ".csv"
        print(fname_csv)

        self.full_df.to_csv(fname_csv, sep=',')

        # for fname in fnames:
        #     getFullLog = 1
        #     processed_f_name, t, df = LogReader.read_one_file(fname, getFullLog)
        #     print("df:", df.shape)

        #     f = os.path.splitext(fname)

        #     fname_csv = f[0] + ".csv"
        #     print(fname_csv)

        #     df.to_csv(fname_csv, sep=',')


    def btn_clicked_sim(self):
        None                        

    def btn_clicked_close_ok(self):
        self.btn_clicked_load()

        # fname_raw = self.edit_sel_file.toPlainText()

        # fnames = fname_raw.split()
        # print("fname:", fnames)

        # dfs = []
        # for fname in fnames:
        #     df_tmp = self.full_df
        #     getFullLog = 1
        #     processed_f_name, t, df = LogReader.read_one_file(fname, getFullLog)
        #     print("df:", df.shape)
        #     dfs.append(df)

        # self.full_df = pd.concat(dfs, ignore_index=True)
        # print('full_df:', self.full_df.shape)

        self.close()

    def btn_clicked_close_cancel(self):
        self.close()

##############################
# folder select window
##############################
class W_FolderSelect(QDialog):
    def __init__(self):
        super().__init__()

        # total layout
        total_layout = QVBoxLayout()
        self.setLayout(total_layout)    # 전체 layout 설정

        # Text Widget for folder selection
        total_layout.addWidget(self.VTextEditWidget())

        # button widget 
        total_layout.addWidget(self.HbuttonWidget())

        # state widget
        self.label_status = QLabel("STATUS")
        # self.label_status.setStyleSheet("border: 1px solid black;") 
        
        # add state widget
        total_layout.addWidget(self.label_status)

        ##########################
        # data frame
        self.full_df = None

    def VTextEditWidget(self):
        gb = QGroupBox('Select destination folder')
        box = QVBoxLayout()

        # # label 'File to process'
        # self.label_sel_file = QLabel('Set Destincation Folder', self)
        # font_dir = self.label_sel_file.font()
        # font_dir.setPointSize(12)
        # font_dir.setFamily('Times New Roman')
        # font_dir.setBold(True)
        # self.label_sel_file.setFont(font_dir)

        # plain text edit
        self.edit_sel_folder = QTextEdit()
        # fname = QDir.toNativeSeparators(r"E:\22_AVP_LOG\AVP_LOG_dmz-20231103")
        fname = QDir.toNativeSeparators(G_DEFAULT_FOLDER_PATH)
        self.edit_sel_folder.setPlainText(fname)

        # btn
        self.btn_proc_data = QPushButton('Select folder', self)
        self.btn_proc_data.clicked.connect(self.btn_sel_folder)

        # box.addWidget(self.label_sel_file)
        box.addWidget(self.edit_sel_folder)
        box.addWidget(self.btn_proc_data)
        gb.setLayout(box)
        return gb

    def btn_sel_folder(self):
        # QFileDialog information
        # https://newbie-developer.tistory.com/122
        # dir = QDir.toNativeSeparators(r"E:\22_AVP_LOG\AVP_LOG_dmz-20231103")
        dir = QDir.toNativeSeparators(G_DEFAULT_FOLDER_PATH)
        # filter = "Index Files (*.idx);;Text Files (*.txt);;All Files (*)"
        # fnames, _ = QFileDialog.getOpenFileNames(self, "Select foler", dir, filter)
        folder_name = QFileDialog.getExistingDirectory(self, "Select foler", dir)
        print(folder_name)
        f_name_native = QDir.toNativeSeparators(folder_name)
        print(f_name_native)
        # edit_names = ""
        # for fname in fnames:
        #     edit_names += fname + "\n"
        self.edit_sel_folder.setPlainText(f_name_native)


    def HbuttonWidget(self):
        gb = QGroupBox('Select File or Folder')
        box = QHBoxLayout()

        self.btn_files = QPushButton('Process folder', self)
        self.btn_files.clicked.connect(self.btn_proc_folder)

        self.btn_folder = QPushButton('None', self)
        self.btn_folder.clicked.connect(self.dialog_open_folder)
        # self.btn.setGeometry(10, 10, 200, 50)   # x, y, w, h

        box.addWidget(self.btn_files)
        box.addWidget(self.btn_folder)
        gb.setLayout(box)
        return gb
    
    def btn_proc_folder(self):
        folder_name = self.edit_sel_folder.toPlainText()
        LogReporter.ROOT_LOG_DIR = folder_name
        LogReporter.TARGET_YEAR = 2023
        LogReporter.GET_FULL_LOG = 0
        limit_n_files = -1   # max number of new files. -1:max, 0:no new file
        LogReporter.Worker(LogReporter.ROOT_LOG_DIR, limit_n_files)
        
   
    def dialog_open_folder(self):
        None



##############################
# folder select window
##############################
class W_Analysis(QDialog):
    def __init__(self):
        super().__init__()

        # total layout
        ly_total = QVBoxLayout()

        ###########################################
        # layout total right
        ###########################################

        # group 1
        gb = QGroupBox('Graph List')
        box = QVBoxLayout()
        
        self.plt_velocity = pg.PlotWidget(title="Velocity")
        self.plt_velocity.plotItem.setLabels(bottom='Index', left='Velocity')
        self.plt_velocity.plotItem.getAxis('bottom').setPen(pg.mkPen(color='#000000'))
        self.plt_velocity.plotItem.getAxis('left').setPen(pg.mkPen(color='#000000'))
        self.plt_velocity.setBackground('w')
        self.plt_velocity.setStyleSheet("border: 1px solid black; padding-left:10px; padding-right:10px;")
        self.pl_pen_velocity = self.plt_velocity.plot(pen='b')

        self.plt_accel = pg.PlotWidget(title="Acceleration")
        self.plt_accel.plotItem.setLabels(bottom='Index', left='Acceleration')
        self.plt_accel.plotItem.getAxis('bottom').setPen(pg.mkPen(color='#000000'))
        self.plt_accel.plotItem.getAxis('left').setPen(pg.mkPen(color='#000000'))
        self.plt_accel.setBackground('w')
        self.plt_accel.setStyleSheet("border: 1px solid black; padding-left:10px; padding-right:10px;")
        self.pl_pen_acceleration = self.plt_accel.plot(pen='b')
        self.pl_pen_accel2 = self.plt_accel.plot(pen='r')

        self.plt_bpressure = pg.PlotWidget(title="Brake Pressure")
        self.plt_bpressure.plotItem.setLabels(bottom='Index', left='Brake Pressure')
        self.plt_bpressure.plotItem.getAxis('bottom').setPen(pg.mkPen(color='#000000'))
        self.plt_bpressure.plotItem.getAxis('left').setPen(pg.mkPen(color='#000000'))
        self.plt_bpressure.setBackground('w')
        self.plt_bpressure.setStyleSheet("border: 1px solid black; padding-left:10px; padding-right:10px;")
        self.pl_pen_pbressure = self.plt_bpressure.plot(pen='b')

        box.addWidget(self.plt_velocity)
        box.addWidget(self.plt_accel)
        box.addWidget(self.plt_bpressure)
        gb.setLayout(box)

        ly_total.addWidget(gb)


        #############################
        # set total layout
        self.setLayout(ly_total)    # 전체 layout 설정
        # container = QWidget()
        # container.setLayout(ly_total)
        # self.setCentralWidget(container)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(300, 300, 1600, 600)    # x,y,w,h
        self.setWindowTitle('Main Window')

        # ly_total = QVBoxLayout()
        ly_total = QHBoxLayout()
        ly_total_l = QVBoxLayout()
        ly_total_r = QVBoxLayout()

        ly_total.addLayout(ly_total_l)
        ly_total.addLayout(ly_total_r)

        #####################################
        # layout total left
        #####################################

        gb = QGroupBox('Select File or Folder')
        box = QHBoxLayout()

        self.btn_files = QPushButton('Select Logfiles', self)
        self.btn_files.clicked.connect(self.dialog_open)

        self.btn_folder = QPushButton('Select Folders', self)
        self.btn_folder.clicked.connect(self.dialog_open_folder)
        # self.btn.setGeometry(10, 10, 200, 50)   # x, y, w, h

        box.addWidget(self.btn_files)
        box.addWidget(self.btn_folder)
        gb.setLayout(box)
        ly_total_l.addWidget(gb)

        # pyqtgraph 
        self.plt_loc = pg.PlotWidget(title="Location")
        self.plt_loc.plotItem.setLabels(bottom='Latitude', left='Longitude')
        self.plt_loc.plotItem.getAxis('bottom').setPen(pg.mkPen(color='#000000'))
        self.plt_loc.plotItem.getAxis('left').setPen(pg.mkPen(color='#000000'))
        self.plt_loc.setBackground('w')
        self.plt_loc.setStyleSheet("border: 1px solid black; padding-left:10px; padding-right:10px;")
        self.pl_pen = self.plt_loc.plot(pen='b')

        self.qTimer = QTimer()
        self.qTimer.timeout.connect(self.draw_chart)
        # self.qTimer.start(25) 
        # self.qTimer.start(500)   # mesc
        self.qTimer.stop()
        self.paused = True

        # button 'Pause/Restart'
        self.btn_pause = QPushButton(text="Draw/Pause")
        self.btn_pause.clicked.connect(self.btn_clicked_pause)

        # button 'Analysis'
        self.btn_analysis = QPushButton(text="Analysis")
        self.btn_analysis.clicked.connect(self.dialog_open_analysis)

        # button 'Analysis'
        self.btn_cal_dist = QPushButton(text="Calculate Distance")
        self.btn_cal_dist.clicked.connect(self.btn_clicked_cal_dist)        

        layout_btns = QHBoxLayout()
        layout_btns.addWidget(self.btn_pause)
        layout_btns.addWidget(self.btn_analysis)
        layout_btns.addWidget(self.btn_cal_dist)

        box = QVBoxLayout()
        # box.addWidget(self.label_main)
        box.addWidget(self.plt_loc)
        box.addLayout(layout_btns)
        box.setSpacing(10)
        box.setContentsMargins(20, 20, 20, 20)

        self.label_status_main = QLabel("STATUS_MAIN")
        

        # ly_total_l.addWidget(self.btn)
        ly_total_l.addLayout(box)
        ly_total_l.addWidget(self.label_status_main)

        # self.setLayout(ly_total)    # total layout 설정
        # self.show()

        ###########################################
        # layout total right
        ###########################################

        # group 1
        gb = QGroupBox('Graph List')
        box = QVBoxLayout()
        
        self.plt_mode = pg.PlotWidget(title="Mode")
        self.plt_mode.plotItem.setLabels(bottom='Index', left='Mode')
        self.plt_mode.plotItem.getAxis('bottom').setPen(pg.mkPen(color='#000000'))
        self.plt_mode.plotItem.getAxis('left').setPen(pg.mkPen(color='#000000'))
        self.plt_mode.setBackground('w')
        self.plt_mode.setStyleSheet("border: 1px solid black; padding-left:10px; padding-right:10px;")
        self.pl_pen_mode = self.plt_mode.plot(pen='b')

        self.plt_h = pg.PlotWidget(title="Heading")
        self.plt_h.plotItem.setLabels(bottom='Index', left='Heading')
        self.plt_h.plotItem.getAxis('bottom').setPen(pg.mkPen(color='#000000'))
        self.plt_h.plotItem.getAxis('left').setPen(pg.mkPen(color='#000000'))
        self.plt_h.setBackground('w')
        self.plt_h.setStyleSheet("border: 1px solid black; padding-left:10px; padding-right:10px;")
        self.pl_pen_h = self.plt_h.plot(pen='b')


        box.addWidget(self.plt_mode)
        box.addWidget(self.plt_h)
        gb.setLayout(box)
        ly_total_r.addWidget(gb)

        # group 2
        gb = QGroupBox('Label List')
        box = QVBoxLayout()        

        self.label_scroll = QScrollArea()
        self.label_scroll.setFixedSize(800, 200)

        self.label_distance = QLabel("distance")
        self.label_distance.setFixedSize(600, 200)

        self.label_scroll.setWidget(self.label_distance)

        box.addWidget(self.label_scroll)

        gb.setLayout(box)
        ly_total_r.addWidget(gb)

        # out groupbox
        self.label_status_main_r = QLabel("STATUS_MAIN_RIGHT")


        ly_total_r.addWidget(self.label_status_main_r)

        container = QWidget()
        container.setLayout(ly_total)
        self.setCentralWidget(container)

        self.dialog_fileselect = W_FileSelect()
        self.dialog_folder_select = W_FolderSelect()
        self.dialog_analysis = W_Analysis()        

    def btn_clicked_pause(self):
        self.toggle_event()

    def btn_clicked_analysis(self):
        None
            
    def btn_clicked_cal_dist(self):
        #################################
        # Calculate all_automode

        #################################
        # 1. load all data
        self.vinfo_day_idx  = self.dialog_fileselect.vinfo_day_idx.copy()
        self.vinfo_day_t    = self.dialog_fileselect.vinfo_day_t.copy()
        self.vinfo_day_dfs  = self.dialog_fileselect.vinfo_day_dfs.copy()

        #################################
        # 2. Process one day
        sum_vinfo_all_automode = []
        for i in range(len(self.vinfo_day_idx)):
            # plt.plot(processed_dfs[i].iloc[:,0])
            # plt.show()
            print("vinfo_day_idx:", self.vinfo_day_idx[i])
            res = LogReporter.process_one_day(self.vinfo_day_idx[i], self.vinfo_day_t[i], self.vinfo_day_dfs[i])
            sum_vinfo_all_automode.append(res)

        print("- All Auto Mode Results: ")
        print("(vinfo, t_start, t_end, loc_start, loc_end, clusterNo, idx_s, idx_e, reason_mode, distance)")
        #for i in range(len(sum_vinfo_all_automode)):
        #        print(*sum_vinfo_all_automode[i], sep='\n')
        #################################
        # 3. Summary the results
        ##############################
        # 날짜별 주행거리 합산
        dist_day = 0
        sum_vinfo_idx = []
        sum_vinfo_day = []
        for i in range(len(sum_vinfo_all_automode)):
            res = sum_vinfo_all_automode[i]
            vinfo_day = res[0][0]
            sum_vinfo_idx.append(vinfo_day)     # vinfo_day
            dist_day = 0
            for j in range(len(res)):
                dist_day += res[j][9] 
            
            # dist_day  = math.trunc(dist_day/100)/10   # 00.0
            dist_day  = math.trunc(dist_day/10)/100     # 00.00
            sum_vinfo_day.append([vinfo_day, dist_day])

        sum_vinfo_day.sort()

        print("- Result per Day(km)")
        print(*sum_vinfo_day, sep='\n')

        #label->setText(label->text() + " some other text");
        self.label_distance.setText(self.label_distance.text()+"- Result per Day(km)\n")
        msg_day = ''
        for v, d in sum_vinfo_day:
            msg_day += ', '.join(v)+': '+str(d)+'\n'     # ',' join seperator
        self.label_distance.setText(self.label_distance.text()+msg_day)
        self.label_distance.repaint()
        self.show()

        ##############################
        # 월별 주행거리 합산
        vinfo_month_prev = []
        dist_month = [] 
        sum_vinfo_month = []
        for i in range(len(sum_vinfo_day)):
            sum_vinfo = sum_vinfo_day[i]
            vinfo_month = sum_vinfo[0][0:-1]
            dist = sum_vinfo[1]
            try:
                idx = vinfo_month_prev.index(vinfo_month)
                dist_month[idx] += dist
                dist_month[idx]  = math.trunc(dist_month[idx]*10)/10.0
            except:
                #no index
                #print("Add new vinfo_month", vinfo_month)
                vinfo_month_prev.append(vinfo_month)
                dist_month.append(dist)

        for i in range(len(vinfo_month_prev)):
            # append the final month
            sum_vinfo_month.append([vinfo_month_prev[i], dist_month[i]])

        sum_vinfo_month.sort()

        print("- Result per Month(km)")
        print(*sum_vinfo_month, sep='\n')

        ##############################
        # 반기별, 전체 주행거리 합산
        # ('vt10', 'id01', '2021', '09') --> ('vt10', 'id01', '2021')
        #vinfo_year_prev = sum_vinfo_month[0][0][0:-1]
        vinfo_year_prev = []
        dist_1st_half = []
        dist_2nd_half = []
        dist_year = []
        sum_vinfo_year = []
        for i in range(len(sum_vinfo_month)):
            sum_vinfo = sum_vinfo_month[i]
            vinfo_year = sum_vinfo[0][0:3]     # ('vt10', 'id01', '2021')
            vinfo_month = sum_vinfo[0][3]
            month = int(vinfo_month)
            dist = sum_vinfo[1]
            try:
                idx = vinfo_year_prev.index(vinfo_year)
                dist_year[idx] += dist
                dist_year[idx]  = math.trunc(dist_year[idx]*10)/10.0
                if month <= 6:
                    dist_1st_half[idx] += dist
                    dist_1st_half[idx]  = math.trunc(dist_1st_half[idx]*10)/10.0
                else:
                    dist_2nd_half[idx] += dist
                    dist_2nd_half[idx]  = math.trunc(dist_2nd_half[idx]*10)/10.0
            except:
                vinfo_year_prev.append(vinfo_year)
                dist_year.append(dist)
                if month <= 6:
                    dist_1st_half.append(dist)
                    dist_2nd_half.append(0.0)
                else:
                    dist_1st_half.append(0.0)
                    dist_2nd_half.append(dist)

        for i in range(len(vinfo_year_prev)):
            # append the final month
            sum_vinfo_year.append([vinfo_year_prev[i], dist_1st_half[i], dist_2nd_half[i], dist_year[i]])
                
        sum_vinfo_year.sort()

        print("- Result per Year(km): 1st half, 2nd half, full year")
        print(*sum_vinfo_year, sep='\n')


    def toggle_event(self):
        # Control animation. Pause/Restart
        if self.paused:
            self.qTimer.start(1000)
        else:
            self.qTimer.stop()
        self.paused = not self.paused

    def draw_chart(self):
        """
        Update plot data
        """
        data_x = self.dialog_fileselect.full_df.iloc[:,15].values.tolist()
        data_y = self.dialog_fileselect.full_df.iloc[:,16].values.tolist()
        print('Len(x,y):', len(data_x), len(data_y))
        self.pl_pen.setData(x=data_x, y=data_y)


        d_time = self.dialog_fileselect.full_df.iloc[:,4].values.tolist()
        d_idx = range(len(d_time))
        d_mode = self.dialog_fileselect.full_df.iloc[:,5].values.tolist()
        # self.pl_pen_mode.setData(x=d_time, y=d_mode)
        self.pl_pen_mode.setData(x=d_idx, y=d_mode)

        d_h = self.dialog_fileselect.full_df.iloc[:,17].values.tolist()
        self.pl_pen_h.setData(x=d_idx, y=d_h)

        self.label_status_main.setText('Len: %d, %d' % (len(data_x), len(data_y)))
        self.label_status_main.repaint()

        d_vel = self.dialog_fileselect.full_df.iloc[:,18].values.tolist()
        self.dialog_analysis.pl_pen_velocity.setData(x=d_idx, y=d_vel)

        d_body_accel_x = self.dialog_fileselect.full_df.iloc[:,33].values.tolist()
        d_body_accel_y = self.dialog_fileselect.full_df.iloc[:,34].values.tolist()
        # 1st graph
        self.dialog_analysis.pl_pen_acceleration.setData(x=d_idx, y=d_body_accel_x)
        # 2nd graph
        self.dialog_analysis.pl_pen_accel2.setData(x=d_idx, y=d_body_accel_y)
        # pen1 = self.dialog_analysis.plt_accel.plot(pen='r')
        # pen1.setData(x=d_time, y=d_body_accel_y)

        d_bpressure = self.dialog_fileselect.full_df.iloc[:,70].values.tolist()
        self.dialog_analysis.pl_pen_pbressure.setData(x=d_idx, y=d_bpressure)        


    # @Slot()
    # def get_data(self):
    #     """
    #     Separating plotting data from entire data.
    #     """
    #     g_data_lock.acquire()
    #     # if len(g_entire_data) > 100:
    #     #     self.graph_data = g_entire_data[len(g_entire_data) - 100:]
    #     # else:
    #     #     self.graph_data = g_entire_data

    #     self.plt_loc.append(np.random.rand())

    #     g_data_lock.release()
    #     self.draw_chart()

    def dialog_open(self):
        self.dialog_fileselect.setWindowTitle('File Select Dialog')
        # always on top
        # self.dialog_fileselect.setWindowModality(Qt.ApplicationModal)
        self.dialog_fileselect.resize(1000, 200)
        self.dialog_fileselect.show()

    def dialog_open_folder(self):
        self.dialog_folder_select.setWindowTitle('Folder Select Dialog')
        # always on top
        # self.dialog_fileselect.setWindowModality(Qt.ApplicationModal)
        self.dialog_folder_select.resize(500, 200)
        self.dialog_folder_select.show()
        
    def dialog_open_analysis(self):
        self.dialog_analysis.setWindowTitle('Analysis Dialog')
        # always on top
        # self.dialog_fileselect.setWindowModality(Qt.ApplicationModal)
        self.dialog_analysis.resize(500, 200)
        self.dialog_analysis.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())   # app.exec_() also OK.




##################################

# r"string": python raw string
# ROOT_LOG_DIR = r"E:\AVP_LOG_dmz_20220110"
# ROOT_LOG_DIR = "/home/etri01/AVP_LOG_dmz-20220331"
# ROOT_LOG_DIR = r"E:\AVP_LOG_dmz_20220110"
#ROOT_LOG_DIR = r"D:\home\etri01\AVP_LOG"

ROOT_LOG_DIR = r"C:\home\etri01\sda1\AVP_LOG_tmp"
ROOT_LOG_DIR = r"D:\home\etri01\sda1\AVP_LOG\VT40-ID01"
TARGET_YEAR = "2023"

GET_FULL_LOG = 0    # 0: only long, lati, 1: get full log data for analysis

##################################


if os.name == 'nt':
    DIR_SEP = "\\"
else:
    DIR_SEP = "/"


def get_dist_vel(t_diff, x, y, x_prev, y_prev):
    x_diff = x - x_prev
    y_diff = y - y_prev

    # unit: meter
    dist = np.sqrt( x_diff*x_diff + y_diff*y_diff)

    vel = dist / t_diff     # m/s
    return dist, vel

# global variable, 
vkeyDic = {}
entire_log_files = []
def search_new_file(dirname, processed_files):
    try:
        filenames = os.listdir(dirname)
        for filename in filenames:
            #print(filename.split('-'))
            full_filename = os.path.join(dirname, filename)
            
            if SKIP_VIRTUAL_VEHICLE:
                try:
                    vid = filename.split('-')[1]
                    if vid == "ID00":
                        # virtual vehicle
                        print("- SKIP: VIRTUAL_VEHICLE:", full_filename)
                        continue                    
                except:
                    None

            # skip the processed files
            if full_filename in processed_files:
                print("- SKIP: processed file:", full_filename)
                continue

            if os.path.isdir(full_filename):
                search_new_file(full_filename, processed_files)
            else:
                # splittext: split file extension
                f, ext = os.path.splitext(full_filename)
                if ext == '.idx': 
                    if f[-5:] == '-lane':
                        continue
                    else:
                        #print(full_filename)
                        entire_log_files.append(full_filename)
    except PermissionError:
        pass
    
    #print(vkeyDic)
    return entire_log_files

def getDistwLine(p1,a,b,c):

    x1, y1 = p1[0], p1[1]

    d = np.abs(a*x1 + b*y1 +c) / np.sqrt(a*a + b*b)

    return d

def getAzimuth(p1, p2):
    x1, y1 = p1[0], p1[1]
    x2, y2 = p2[0], p2[1]
    # slope
    dy = y2-y1
    dx = x2-x1

    # m = dy/dx
    # n = y1 - m*x1

    yaw = np.arctan2(dy,dx)
    yaw = (yaw + np.pi) % (2.0*np.pi) - np.pi   # -180<yaw<180
    azimuth = np.pi/2 - yaw
    if (azimuth<0):
        azimuth += 2.0*np.pi

    azimuth_deg = azimuth*180/np.pi
    # print("yaw:", yaw *180/np.pi)
    # print("azimuth:", azimuth*180/np.pi)

    return azimuth_deg

def getLine(p1, p2):
    x1, y1 = p1[0], p1[1]
    x2, y2 = p2[0], p2[1]
    # slope
    dy = y2-y1
    dx = x2-x1
    if dx == 0:
        dx = 0.00000001
    m = dy/dx
    n = y1 - m*x1

    yaw = np.arctan2(dy,dx)
    yaw = (yaw + np.pi) % (2.0*np.pi) - np.pi   # -180<yaw<180
    azimuth = np.pi/2 - yaw
    if (azimuth<0):
        azimuth += 2.0*np.pi

    print("yaw:", yaw *180/np.pi)
    print("azimuth:", azimuth*180/np.pi)

    # y = m*x + n --> mx -y + n = 0
    return m, -1, n

def getAzimuth(p1, p2):
    x1, y1 = p1[0], p1[1]
    x2, y2 = p2[0], p2[1]
    # slope
    dx = x2-x1
    dy = y2-y1

    # m = dy/dx
    # n = y1 - m*x1

    yaw = np.arctan2(dy,dx)
    yaw = (yaw + np.pi) % (2.0*np.pi) - np.pi   # -180<yaw<180
    azimuth = np.pi/2 - yaw
    if (azimuth<0):
        azimuth += 2.0*np.pi

    azimuth_deg = azimuth*180/np.pi
    # print("yaw:", yaw *180/np.pi)
    # print("azimuth:", azimuth*180/np.pi)

    return azimuth_deg

def getAzimuthFromVec(x, y):
    # slope
    dx = x
    dy = y

    # m = dy/dx
    # n = y1 - m*x1
    yaw = np.arctan2(dy,dx)
    yaw = (yaw + np.pi) % (2.0*np.pi) - np.pi   # -180<yaw<180
    azimuth = np.pi/2 - yaw
    if (azimuth<0):
        azimuth += 2.0*np.pi

    azimuth_deg = azimuth*180/np.pi
    # print("yaw:", yaw *180/np.pi)
    # print("azimuth:", azimuth*180/np.pi)

    return azimuth_deg

def ShowFigure(df, t_all, idx_s, idx_e):

    t = t_all[idx_s: idx_e]
    # t = list(range(df.shape[0]))


    # plt.figure("SAS")
    # fig = plt.figure()
    # ax = plt.subplot2grid((4, 1), (0, 0), rowspan=2)
    # ax1 = plt.subplot2grid((4, 1), (2, 0))
    # ax2 = plt.subplot2grid((4, 1), (3, 0))

    ###############
    # time
    # base_t = 0  # 8:29:00     
    # t_1 = list(map(lambda x:(x/1000-base_t), t))
    # t_1 = list(map(hhmmss2sec, t_all))

    col_t = 4

    col_fd_sas = 82
    col_vislong = 40
    col_vislati = 41
    col_vish = 42
    col_invehi_vel_rl = 83
    col_invehi_vel_rr = 84
    col_x_est = 67
    col_y_est = 68
    col_yaw_est = 69

    base_t = 0  # 8:29:00     
    t_recv = df.iloc[idx_s:idx_e, col_t].to_list()
    t_ticks = list(map(lambda x:(x/1000-base_t), t_recv))

    t_tick = list(range(idx_e-idx_s))
    t_1 = list(map(lambda x:(x/100), t_tick))

    col_tg_sas = 114
    col_fd_sas = 82
    col_long = 67
    col_lati = 68
    col_heading = 69
    col_mode = 5
    col_reasomMode = 6

    col_long_gps = 18
    col_lati_gps = 19
    col_azi_gps = 20

    mode = df.iloc[idx_s:idx_e, col_mode].to_list()
    reason_mode = df.iloc[idx_s:idx_e, col_reasomMode].to_list()

    z_long = df.iloc[idx_s:idx_e, col_vislong].to_list()
    z_lati = df.iloc[idx_s:idx_e, col_vislati].to_list()

    x_est= df.iloc[idx_s:idx_e, col_x_est].to_list()
    y_est = df.iloc[idx_s:idx_e, col_y_est].to_list()

    long_gps = df.iloc[idx_s:idx_e, col_long_gps].to_list()
    lati_gps = df.iloc[idx_s:idx_e, col_lati_gps].to_list()

    long_1 = [z_long[0], z_long[-1]]
    lati_1 = [z_lati[0], z_lati[-1]]

    a,b,c = getLine((z_long[0], z_lati[0]), (z_long[-1], z_lati[-1]))
    d_list = []
    for lo, li in zip(z_long, z_lati):
        d = getDistwLine((lo,li), a, b, c)
        d_list.append(d)

    azi_list = []
    lo_0, li_0 = z_long[0], z_lati[0]
    azi_default = getAzimuth((lo_0, li_0), (z_long[-1], z_lati[-1]))
    d_tic = 100
    for i, (lo, li) in enumerate(zip(z_long, z_lati)):
        if i < d_tic:
            a = azi_default
        else:
            prev = i-d_tic
            a = getAzimuth((z_long[prev], z_lati[prev]), (lo, li))
        azi_list.append(a)

    azi_list_10 = []
    lo_0, li_0 = z_long[0], z_lati[0]
    azi_default = getAzimuth((lo_0, li_0), (z_long[-1], z_lati[-1]))
    d_tic = 50
    for i, (lo, li) in enumerate(zip(z_long, z_lati)):
        if i < d_tic:
            a = azi_default
        else:
            prev = i-d_tic
            a = getAzimuth((z_long[prev], z_lati[prev]), (lo, li))
        azi_list_10.append(a)


    ##############################
    # figure 1: Location
    fig, ax = plt.subplots()
    plt.get_current_fig_manager().set_window_title("Location")    
    
    ax.plot(z_long, z_lati, '-o', label='Measured', linewidth=1.0)
    ax.plot(x_est, y_est, '-x',  label='Predicted', linewidth=1.0)
    ax.plot(long_1, lati_1, '-x',  label='Measured', linewidth=1.0)
    # ax.plot(t_1,long, t_1, lati)

    lo_0, li_0 = z_long[0], z_lati[0]

    lo_0_1 = lo_0 - 10
    li_0_1 = li_0 + 10
    # ax.annotate(str(t_ticks[0]),
    #             xy=(lo_0, li_0), xycoords='data',
    #             xytext=(-10, 10), textcoords='offset points',
    #             arrowprops=dict(arrowstyle="->",
    #                             connectionstyle="arc3"),
    #             )
    ax.annotate(str(t_ticks[0]),
                xy=(lo_0, li_0), xycoords='data',
                xytext=(-50, 50), textcoords='offset points',
                arrowprops=dict(arrowstyle="simple",
                                connectionstyle="arc3"),
                )
    ax.annotate(str(t_ticks[-1]),
                xy=(z_long[-1], z_lati[-1]), xycoords='data',
                xytext=(50, 50), textcoords='offset points',
                arrowprops=dict(arrowstyle="simple",
                                connectionstyle="arc3"),
                )                

    ax.axis('equal')
    ax.set_title("Location")
    # plt.get_current_fig_manager().set_window_title("Location")    
    ax.set_xlabel('X(m)') 
    ax.set_ylabel('Y(m)') 
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.grid(True)

    #############################################
    # figure 2: Time-Mode-DistbyAxis-Vel
    #fig, ax = plt.subplots(2, 1, height_ratios=[2,1])  # working over matplotlib 3.6.0
    # fig, ax = plt.subplots(2, 1, gridspec_kw={'height_ratios': [2, 1]})
    fig, ax = plt.subplots(4, 1)
    plt.get_current_fig_manager().set_window_title("Time-Mode-PosByAxis-Vel")    

    ##################
    # Mode 
    axIdx = 0
    # ax[axIdx].plot(t_1, d_list)
    ax[axIdx].plot(t_recv, mode)
    ax[axIdx].set_title("Time-Distance")
    #plt.get_current_fig_manager().set_window_title("Time-Distance")
    #ax[axIdx].set_xlabel('Time(sec)') 
    ax[axIdx].set_ylabel('Mode') 
    ax[axIdx].ticklabel_format(useOffset=False, style='plain')
    ax[axIdx].grid(True)

    #################
    # X axis pose
    axIdx = 1

    # straight line: from start to end
    t_st = [t_recv[0], t_recv[-1]]
    long_st = [z_long[0], z_long[-1]]


    # ax[axIdx].plot(t_1, d_list)
    ax[axIdx].plot(t_recv, z_long, t_st, long_st)
    # ax[axIdx].set_title("Time-Distance")
    #plt.get_current_fig_manager().set_window_title("Time-Distance")
    #ax[axIdx].set_xlabel('Time(sec)') 
    ax[axIdx].set_ylabel('Position X(m)') 
    ax[axIdx].ticklabel_format(useOffset=False, style='plain')
    ax[axIdx].grid(True)

    #################
    # Y axis pose
    axIdx = 2

    # straight line: from start to end
    t_st = [t_recv[0], t_recv[-1]]
    lati_st = [z_lati[0], z_lati[-1]]

    # ax[axIdx].plot(t_1, d_list)
    ax[axIdx].plot(t_recv, z_lati, t_st, lati_st)
    # ax[axIdx].set_title("Time-Distance")
    #plt.get_current_fig_manager().set_window_title("Time-Distance")
    #ax[axIdx].set_xlabel('Time(sec)') 
    ax[axIdx].set_ylabel('Position Y(m)') 
    ax[axIdx].ticklabel_format(useOffset=False, style='plain')
    ax[axIdx].grid(True)


    #################
    # velocity

    col_invehi_vel_rl = 83
    col_invehi_vel_rr = 84
    invehi_vel_rl = df.iloc[idx_s:idx_e, col_invehi_vel_rl].to_list()
    invehi_vel_rr = df.iloc[idx_s:idx_e, col_invehi_vel_rr].to_list()
    invehi_vel = [(x+y)/2 for x,y in zip(invehi_vel_rl, invehi_vel_rr)]

    axIdx = 3

    # ax[axIdx].plot(t_1, d_list)
    ax[axIdx].plot(t_recv, invehi_vel)
    # ax[axIdx].set_title("Time-Distance")
    #plt.get_current_fig_manager().set_window_title("Time-Distance")
    #ax[axIdx].set_xlabel('Time(sec)') 
    ax[axIdx].set_ylabel('Velocity(ego, km/h)') 
    ax[axIdx].ticklabel_format(useOffset=False, style='plain')
    ax[axIdx].grid(True)

    ##############################
    # distance by axis
    fig, ax = plt.subplots(2,1)
    plt.get_current_fig_manager().set_window_title("Distance by Axis")

    t_2 = [t_1[0], t_1[-1]]
    long_2 = [z_long[0], z_long[-1]]
    ax[0].plot(t_1, z_long, t_2, long_2)
    # ax[0].set_xlabel('Time(sec)') 

    ax[0].set_ylabel('X(m)') 
    ax[0].ticklabel_format(useOffset=False, style='plain')
    ax[0].grid(True)

    # fig, ax = plt.subplots()
    t_2 = [t_1[0], t_1[-1]]
    lati_2 = [z_lati[0], z_lati[-1]]
    ax[1].plot(t_1, z_lati, t_2, lati_2)
    ax[1].set_xlabel('Time(sec)') 
    ax[1].set_ylabel('Y(m)') 
    ax[1].ticklabel_format(useOffset=False, style='plain')
    ax[1].grid(True)

    ###############################
    #plt.figure("APS-BPS")
    fig, ax = plt.subplots(2,1)
    plt.get_current_fig_manager().set_window_title("SAS-Heading")
    ###############
    # time
    # base_t = 82900
    # t_1 = list(map(lambda x:(x/1000-base_t), t))
    # t_1 = list(map(hhmmss2sec, t_all))

    ###############
    # target brake
    heading = df.iloc[idx_s:idx_e, col_vish].to_list() 

    tg_sas = df.iloc[idx_s:idx_e, col_tg_sas].to_list() 
    tg_sas = list(map(lambda x:x/10.0, tg_sas))
    fd_sas = df.iloc[idx_s:idx_e, col_fd_sas].to_list() 
    fd_sas = list(map(lambda x:x/10.0, fd_sas))

    # azimuth calculation
    azi_gps = df.iloc[idx_s:idx_e, col_azi_gps].to_list()
    # azi_gps_deg = list(map(lambda x:((np.pi/2-x)* 180.0/np.pi), azi_gps))
    azi_gps_deg = copy.deepcopy(azi_gps)
    for i, x in enumerate(azi_gps):
        x = (x + np.pi) % (2.0*np.pi) - np.pi   # -180<yaw<180
        azi = np.pi/2 - x
        if (azi<0):
            azi += 2.0*np.pi
        azi_gps_deg[i] = azi*180.0/np.pi


    azi_list = []
    lo_0, li_0 = z_long[0], z_lati[0]
    azi_default = getAzimuth((lo_0, li_0), (z_long[-1], z_lati[-1]))
    d_tic = 100
    for i, (lo, li) in enumerate(zip(z_long, z_lati)):
        if i < d_tic:
            a = azi_default
        else:
            prev = i-d_tic
            a = getAzimuth((z_long[prev], z_lati[prev]), (lo, li))
        azi_list.append(a)

    azi_list_10 = []
    lo_0, li_0 = z_long[0], z_lati[0]
    azi_default = getAzimuth((lo_0, li_0), (z_long[-1], z_lati[-1]))
    d_tic = 50
    for i, (lo, li) in enumerate(zip(z_long, z_lati)):
        if i < d_tic:
            a = azi_default
        else:
            prev = i-d_tic
            a = getAzimuth((z_long[prev], z_lati[prev]), (lo, li))
        azi_list_10.append(a)

    # xticks
    #plt.xticks(t_1, t_ticks, rotation=45)


    # fig, ax = plt.subplots()
    ax[0].plot(t_1, tg_sas, label="Target SAS")
    ax[0].plot(t_1, fd_sas, label="Feedback SAS")
    ax[0].set_xlabel('Time(sec)') 
    ax[0].set_ylabel('SAS(deg)') 
    ax[0].ticklabel_format(useOffset=False, style='plain')
    ax[0].legend()
    ax[0].grid(True)

    ax[1].plot(t_1, heading, label="VO_H")
    ax[1].plot(t_1, azi_list, label="Tic100")
    ax[1].plot(t_1, azi_list_10, label="Tic50")
    ax[1].plot(t_1, azi_gps_deg, label="GPS")
    ax[1].set_xlabel('Time(sec)') 
    ax[1].set_ylabel('Heading(deg)') 
    # no scientific notation: 
    # https://stackoverflow.com/questions/28371674/prevent-scientific-notation-in-matplotlib-pyplot
    ax[1].ticklabel_format(useOffset=False, style='plain')
    ax[1].legend()
    ax[1].grid(True)

    ######################
    # X: Position, Velocity, Acceleration
    fig, ax = plt.subplots(3,1)

    # position
    axi = 0
    ax[0].set_title('P, V, A by World Coordinate X')
    ax[0].plot(t_1, mode, '-x', label='Mode')
    ax[0].plot(t_1, reason_mode, '-x', label='Reason Mode')
    ax[0].set_xlabel('Time(sec)') 
    ax[0].set_ylabel('X(m)')     
    ax[0].ticklabel_format(useOffset=False, style='plain')
    ax[0].legend(loc='best')
    ax[0].grid(True)
    # # velocity
    # ax[1].plot(t_1, x1, '-x', label='Predicted')
    # ax[1].plot(t_1, z_vel_x, '-x', label='Measured by Wspd, VoSS_H')
    # ax[1].set_xlabel('Time(sec)') 
    # ax[1].set_ylabel('Velocity(m/s)')     
    # ax[1].ticklabel_format(useOffset=False, style='plain')
    # ax[1].legend(loc='best')
    # ax[1].grid(True)
    # # acceleration
    # ax[2].plot(t_1, x2)
    # ax[2].set_xlabel('Time(sec)') 
    # ax[2].set_ylabel('Acceleration($m/s^2$)')     
    # ax[2].ticklabel_format(useOffset=False, style='plain')
    # ax[2].legend(loc='best')
    # ax[2].grid(True)

    plt.draw()
    plt.show(block=False)
    plt.pause(0.1)
    input("hit[Enter] to Continue")
    plt.close('all')

    # plt.show()


#     col_t = 4
#     col_fd_sas = 82
#     col_long = 67
#     col_lati = 68
#     col_heading = 69
#     col_invehi_vel_rl = 83
#     col_invehi_vel_rr = 84
#     z_t = df.iloc[idx_s:idx_e, col_t].to_list()
#     z_long = df.iloc[idx_s:idx_e, col_long].to_list()
#     z_lati = df.iloc[idx_s:idx_e, col_lati].to_list()    
#     z_heading = df.iloc[idx_s:idx_e, col_heading].to_list()    
#     z_sas = df.iloc[idx_s:idx_e, col_fd_sas].to_list()    # deg *10
#     # velocity
#     z_whspd_rl = df.iloc[idx_s:idx_e, col_invehi_vel_rl].to_list()
#     z_whspd_rr = df.iloc[idx_s:idx_e, col_invehi_vel_rr].to_list()
#     z_vel_kph = list(map(lambda x,y:((x+y)/2), z_whspd_rl, z_whspd_rr ))    # left+right --> center
#     z_vel = list(map(lambda x:x*0.03125 /3.6, z_vel_kph))   # m/s

#     z_vel_x = list(map(lambda x,y:(x*np.cos((90-y)*np.pi/180)), z_vel, z_heading))
#     z_vel_y = list(map(lambda x,y:(x*np.sin((90-y)*np.pi/180)), z_vel, z_heading))

#     z_yaw_deg = list(map(lambda x:(90-x), z_heading))   # 0~360 --> -90+270
# #    (z_yaw[i]+np.pi) % (2.0*np.pi) - np.pi    # +-180
#     z_yaw_deg = list(map(lambda x:((x+180.0)%360.0-180.0), z_yaw_deg))    # -90+270 --> -180+180
#     z_yaw = list(map(lambda x:(x*np.pi/180), z_yaw_deg))


#     # ######################
#     # # X: Position, Velocity, Acceleration
#     # fig, ax = plt.subplots(3,1)
#     # t_tick = list(range(idx_e-idx_s))
#     # t_1 = list(map(lambda x:(x/100), t_tick))
#     # # position
#     # axi = 0
#     # ax[0].set_title('P, V, A by World Coordinate X')
#     # ax[0].plot(t_1, z_heading, '-x', label='Heading')
#     # ax[0].plot(t_1, z_yaw_deg, '-x', label='Yaw(deg)')
#     # ax[0].plot(t_1, z_yaw, '-x', label='Yaw(rad)')
#     # ax[0].set_xlabel('Time(sec)') 
#     # ax[0].set_ylabel('X(m)')     
#     # ax[0].ticklabel_format(useOffset=False, style='plain')
#     # ax[0].legend(loc='best')
#     # ax[0].grid(True)

#     # plt.show()

#     sasRatio = 18.9    # 
#     sasBias = 12.0      # sas bias, unit, deg*10
#     vSpecL = 2.7        # wheelbase, m
#     z_fwangle_deg= list(map(lambda x:(x+sasBias)/10/sasRatio, z_sas))  # sas --> fwangle, deg
#     z_fwangle = list(map(lambda x:(x*np.pi/180), z_fwangle_deg))  # sas --> fwangle, deg
#     z_yawrate = list(map(lambda f,v:(v*np.tan(f)/vSpecL), z_fwangle, z_vel))  # fwangle --> yawrate
#     z_yawrate_deg = list(map(lambda x:(x*180/np.pi), z_yawrate))  # yawrate,rad --> deg

#     dt = 0.01   # Sample Rate of the Measurements is 50Hz
#     # P, Q, R = initKF(dt)

#     x0 = []
#     x1 = []
#     x2 = []
#     y0 = []
#     y1 = []
#     y2 = []    
#     Px0 = []
#     Px1 = []
#     Px2 = []
#     yaw0 = []
#     yaw1 = []
#     yaw2 = []
#     yaw3 = []
#     yaw4 = []
#     yaw5 = []

#     KF_x = KF1D()
#     KF_y = KF1D()
#     KF_yaw = KFyaw()

#     # Initial State
#     # x = np.array([[z_long[0], 0, 0]]).T
#     # y = np.array([[z_lati[0], 0, 0]]).T
#     x = np.array([[z_long[0], z_vel_x[0], 0]]).T
#     y = np.array([[z_lati[0], z_vel_y[0], 0]]).T
#     # radian, m/s
#     yaw = np.array([[z_yaw[0], z_yawrate[0], z_fwangle[0], 0.0, z_vel[0], 0.0]]).T
#     print("init X=", x, x.shape)

#     zx = np.array([[z_long[0], z_vel_x[0]]]).T
#     zy = np.array([[z_long[0], z_vel_x[0]]]).T    
#     zyaw = np.array([[z_yaw[0], z_yawrate[0], z_fwangle[0], z_vel[0]]]).T

#     Px = KF_x.P_0   
#     Py = KF_y.P_0
#     Pyaw = KF_yaw.P_0
#     for i in range(len(z_long)):

#         # # # Time Update (Prediction)
#         # # # ========================
#         # # # Project the state ahead
#         # # # see "Dynamic Matrix"
#         # x, P = prediction(x, P, Q, dt)

#         # # # Measurement Update (Correction)
#         # # # ===============================
#         # # # Measurement Function
#         # x, P, Z, K = correction(x, P, R, m)
#         zx[0] = z_long[i]
#         zx[1] = z_vel_x[i]      # from heading and wheelspd
#         zy[0] = z_lati[i]
#         zy[1] = z_vel_y[i]      # from heading and wheelspd

#         z_yaw[i] =(z_yaw[i]+np.pi) % (2.0*np.pi) - np.pi    # +-180
#         zyaw[0] = z_yaw[i]
#         zyaw[1] = z_yawrate[i]
#         zyaw[2] = z_fwangle[i]
#         zyaw[3] = z_vel[i]

#         x, Px = KF_x.KF(zx, x, Px)
#         y, Py = KF_y.KF(zy, y, Py)
#         yaw, Pyaw = KF_yaw.KF(zyaw, 0.01, yaw, Pyaw)
#         yaw[0] =(yaw[0]+np.pi) % (2.0*np.pi) - np.pi    # +-180        

#         # Save states for Plotting
#         x0.append(float(x[0]))
#         x1.append(float(x[1]))
#         x2.append(float(x[2]))
#         y0.append(float(y[0]))
#         y1.append(float(y[1]))
#         y2.append(float(y[2]))        
#         Px0.append(float(Px[0,0]))
#         Px1.append(float(Px[1,1]))
#         Px2.append(float(Px[2,2]))
#         yaw0.append(float(yaw[0]))
#         yaw1.append(float(yaw[1]))
#         yaw2.append(float(yaw[2]))   
#         yaw3.append(float(yaw[3]))
#         yaw4.append(float(yaw[4]))
#         yaw5.append(float(yaw[5]))   

#     #########################################
#     # Draw plots
#     t_tick = list(range(idx_e-idx_s))
#     t_1 = list(map(lambda x:(x/100), t_tick))
    
#     # fig, ax = plt.subplots()

#     # # position
#     # ax.plot(x0, y0, '-x', label='$Predicted$', linewidth=2.0)
#     # ax.plot(z_long, z_lati, '-x', label='$Measured$', linewidth=1.0)
#     # ax.set_title('Position')
#     # ax.set_xlabel('Longitude(m)') 
#     # ax.set_ylabel('Latitude(m)')     
#     # ax.ticklabel_format(useOffset=False, style='plain')
#     # ax.legend(loc='best')
#     # ax.grid(True)

#     fig = plt.figure(constrained_layout=True)
#     gs = GridSpec(3,1,figure=fig)
#     ax = fig.add_subplot(gs[0:2,0])
#     ax.plot(x0, y0, '-x', label='$Predicted$', linewidth=2.0)
#     ax.plot(z_long, z_lati, '-x', label='$Measured$', linewidth=1.0)
#     ax.set_title('Position')
#     ax.set_xlabel('Longitude(m)') 
#     ax.set_ylabel('Latitude(m)')     
#     ax.ticklabel_format(useOffset=False, style='plain')
#     ax.legend(loc='best')
#     ax.grid(True)

#     azi_list_v = []
#     d_tic = 100
#     azi_default = getAzimuth((x0[0], y0[0]), (x0[-1], y0[-1]))
#     for i, (x,y) in enumerate(zip(z_vel_x, z_vel_y)):   # measured velocity vector
#         if i < d_tic:
#             a = azi_default
#         else:
#             prev = i-d_tic        
#             a = getAzimuthFromVec(x, y)
#         azi_list_v.append(a)

#     azi_list_v_p = []
#     d_tic = 100
#     azi_default = getAzimuth((x0[0], y0[0]), (x0[-1], y0[-1]))
#     for i, (x,y) in enumerate(zip(x1, y1)):   # predicted velocity vector
#         if i < d_tic:
#             a = azi_default
#         else:
#             prev = i-d_tic        
#             a = getAzimuthFromVec(x, y)
#         azi_list_v_p.append(a)

#     ax2 = fig.add_subplot(gs[2,0])
#     ax2.plot(t_1, azi_list_v_p, '-x', label='Predicted', linewidth=1.0)
#     ax2.plot(t_1, azi_list_v, '-o', label='Measured by Wspd & VoSS_H', linewidth=2.0)
#     ax2.plot(t_1, z_heading, '-x', label='Measured by VoSS', linewidth=2.0)
#     ax2.set_title('Heading')
#     ax2.set_xlabel('Time(sec)') 
#     ax2.set_ylabel('Azimuth(deg)')     
#     ax2.ticklabel_format(useOffset=False, style='plain')
#     ax2.legend(loc='best')
#     ax2.grid(True)

#     ######################
#     # X: Position, Velocity, Acceleration
#     fig, ax = plt.subplots(3,1)

#     # position
#     axi = 0
#     ax[0].set_title('P, V, A by World Coordinate X')
#     ax[0].plot(t_1, x0, '-x', label='Predicted')
#     ax[0].plot(t_1, z_long, '-x', label='Measured by Wspd, VoSS_H')
#     ax[0].set_xlabel('Time(sec)') 
#     ax[0].set_ylabel('X(m)')     
#     ax[0].ticklabel_format(useOffset=False, style='plain')
#     ax[0].legend(loc='best')
#     ax[0].grid(True)
#     # velocity
#     ax[1].plot(t_1, x1, '-x', label='Predicted')
#     ax[1].plot(t_1, z_vel_x, '-x', label='Measured by Wspd, VoSS_H')
#     ax[1].set_xlabel('Time(sec)') 
#     ax[1].set_ylabel('Velocity(m/s)')     
#     ax[1].ticklabel_format(useOffset=False, style='plain')
#     ax[1].legend(loc='best')
#     ax[1].grid(True)
#     # acceleration
#     ax[2].plot(t_1, x2)
#     ax[2].set_xlabel('Time(sec)') 
#     ax[2].set_ylabel('Acceleration($m/s^2$)')     
#     ax[2].ticklabel_format(useOffset=False, style='plain')
#     ax[2].legend(loc='best')
#     ax[2].grid(True)

#     ######################
#     # Y: Position, Velocity, Acceleration
#     fig, ax = plt.subplots(3,1)
#     # position
#     ax[0].set_title('P, V, A by World Coordinate Y')
#     ax[0].plot(t_1, y0, '-x',label='$Predicted$')
#     ax[0].plot(t_1, z_lati, '-x', label='Measured by Wspd, VoSS_H')
#     ax[0].set_xlabel('Time(sec)') 
#     ax[0].set_ylabel('Y(m)')     
#     ax[0].ticklabel_format(useOffset=False, style='plain')
#     ax[0].legend(loc='best')
#     ax[0].grid(True)
#     # velocity
#     ax[1].plot(t_1, y1, '-x', label='$Predicted$')
#     ax[1].plot(t_1, z_vel_y, '-x', label='$Measured$')
#     ax[1].set_xlabel('Time(sec)') 
#     ax[1].set_ylabel('Velocity(m/s)')     
#     ax[1].ticklabel_format(useOffset=False, style='plain')
#     ax[1].legend(loc='best')
#     ax[1].grid(True)
#     # acceleration
#     ax[2].plot(t_1, y2)
#     ax[2].set_xlabel('Time(sec)') 
#     ax[2].set_ylabel('Acceleration($m/s^2$)')     
#     ax[2].ticklabel_format(useOffset=False, style='plain')
#     ax[2].legend(loc='best')
#     ax[2].grid(True)

#     ######################
#     # merged
#     fig, ax = plt.subplots(3,1)

#     # # velocity
#     # z_whspd_rl = df.iloc[idx_s:idx_e, col_invehi_vel_rl].to_list()
#     # z_whspd_rr = df.iloc[idx_s:idx_e, col_invehi_vel_rr].to_list()

#     # vel = list(map(lambda x,y:np.sqrt(x*x+y*y), x1, y1))    # x_vel, y_vel --> vel

#     # z_vel_kph = list(map(lambda x,y:((x+y)/2), z_whspd_rl, z_whspd_rr ))
#     # z_vel = list(map(lambda x:x*0.03125 /3.6, z_vel_kph))   # m/s
#     vel = list(map(lambda x,y:np.sqrt(x*x+y*y), x1, y1))    # x_vel, y_vel --> vel

#     # acceleration
#     z_accel = []
#     d_tic = 100
#     for i, z in enumerate(z_vel):
#         if i < d_tic:
#             a = 0.0
#         else:
#             prev = i-d_tic
#             a = (z-z_vel[prev])/(dt*d_tic)
#             #print("z-z_prev:%.02f-%.02f, a=%.02f" % (z, z_vel[prev], a))
#         z_accel.append(a)

#     p_accel = []
#     d_tic = 100
#     for i, p in enumerate(vel):
#         if i < d_tic:
#             a = 0.0
#         else:
#             prev = i-d_tic
#             a = (p-vel[prev])/(dt*d_tic)
#             #print("z-z_prev:%.02f-%.02f, a=%.02f" % (z, z_vel[prev], a))
#         p_accel.append(a)

#     accel = list(map(lambda x,y:np.sqrt(x*x+y*y), x2, y2))  # x_acc, y_acc --> accel
#     # (yaw + np.pi) % (2.0*np.pi) - np.pi
#     accel_yaw = list(map(lambda x,y:(np.arctan2(y,x)), x2, y2))  # yaw, not azimuth
#     accel_azi = list(map(lambda x:(np.pi/2 - x)*180/np.pi, accel_yaw))
#     accel_angle_diff = list(map(lambda x,y:(x-y+360.0)%360.0, z_heading, accel_azi))  # x_acc, y_acc --> accel_direction
#     accel_sign = list(map(lambda x:(1.0 if x>-180.0 and x<180.0 else -1), accel_angle_diff))  # x_acc, y_acc --> accel_direction
#     accel_w_sign = list(map(lambda x,y:x*y, accel, accel_sign))

#     # velocity
#     ax[0].set_title('Velocity, Acceleration by Vehicle Coordinate')
#     ax[0].plot(t_1, vel, '-x', label='$Predicted$')
#     ax[0].plot(t_1, z_vel, '-x', label='$Wheelspeed$')
#     ax[0].set_xlabel('Time(sec)') 
#     ax[0].set_ylabel('Velocity(m/s)')     
#     ax[0].ticklabel_format(useOffset=False, style='plain')
#     ax[0].legend(loc='best')
#     ax[0].grid(True)
#     # Acceleration
#     ax[1].plot(t_1, p_accel, '-x', label='$Predicted$')
#     ax[1].plot(t_1, z_accel, '-x', label='$Measured$')
#     ax[1].set_xlabel('Time(sec)') 
#     ax[1].set_ylabel('Acceleration($m/s^2$)')     
#     ax[1].ticklabel_format(useOffset=False, style='plain')
#     ax[1].legend(loc='best')
#     ax[1].grid(True)
#     # # acceleration
#     # ax[2].plot(t_1, y2)
#     # ax[2].set_xlabel('Time(sec)') 
#     # ax[2].set_ylabel('Acceleration($m/s^2$)')     
#     # ax[2].ticklabel_format(useOffset=False, style='plain')
#     # ax[2].legend(loc='best')
#     # ax[2].grid(True)

#     ######################
#     # Heading
#     fig, ax = plt.subplots(3,1)

#     azi_list = []
#     lo_0, li_0 = x0[0], y0[0]
#     azi_default = getAzimuth((lo_0, li_0), (x0[-1], y0[-1]))
#     d_tic = 100
#     for i, (lo, li) in enumerate(zip(x0, y0)):
#         if i < d_tic:
#             a = azi_default
#         else:
#             prev = i-d_tic
#             a = getAzimuth((x0[prev], y0[prev]), (lo, li))
#         azi_list.append(a)

#     azi_list_v = []
#     d_tic = 100
#     azi_default = getAzimuth((lo_0, li_0), (x0[-1], y0[-1]))
#     for i, (x,y) in enumerate(zip(x1, y1)):
#         if i < d_tic:
#             a = azi_default
#         else:
#             prev = i-d_tic        
#             a = getAzimuthFromVec(x, y)
#         azi_list_v.append(a)

#     azi_list_sas = []
#     d_tic = 10
#     azi_default = getAzimuth((lo_0, li_0), (x0[-1], y0[-1]))
#     # sasRatio = -18.9    # 
#     # sasBias = 12.0      # sas bias, unit, deg*10
#     # vSpecL = 2.7        # wheelbase, m
#     # z_fwangle = list(map(lambda x:(x+sasBias)/10/sasRatio, z_sas))  # sas --> fwangle
#     # z_yawrate = list(map(lambda f,v:(v/vSpecL*f), z_fwangle, z_vel))  # fwangle --> yawrate
#     for i, yawrate in enumerate(z_yawrate_deg):
#         if i < d_tic:
#             a = azi_default
#         else:
#             a = a + -1*yawrate*dt
#         azi_list_sas.append(a)


#     azi_yaw = list(map(lambda x:((np.pi/2 - x)*180/np.pi), yaw0))   # yaw(+-pi) --> azi(-90~270)
#     azi_yaw = list(map(lambda x:((x+360.0)%360), azi_yaw))  # azi(-90~270) --> azi(0~360)
#     z_yaw_list = []
#     a_prev = 0
#     for i, yawrate in enumerate(z_yawrate_deg):
#         if i < d_tic:
#             a = z_yaw_deg[0]
#             a_prev = a
#         else:
#             # yawrate+ means azimuth-
#             a = a_prev + -1*yawrate*dt
#             a_prev = a
#         z_yaw_list.append(a)

#     # azimuth
#     axi = 0
#     ax[axi].plot(t_1, azi_list, '-x', label='$Predicted by Pose$')
#     ax[axi].plot(t_1, azi_list_v, '-x', label='$Predicted by Vel$')
#     ax[axi].plot(t_1, azi_list_sas, '-x', label='$Predicted by SAS$')
#     ax[axi].plot(t_1, azi_yaw, '-x', label='$Predicted by KFyaw$')
#     ax[axi].plot(t_1, z_heading, '-x', label='$Measured by VoSS$')
#     ax[axi].plot(t_1, z_yaw_deg, '-x', label='$Yaw by VoSS$')
#     ax[axi].plot(t_1, z_yaw_list, '-x', label='$Azi by SAS$')
#     ax[axi].set_xlabel('Time(sec)') 
#     ax[axi].set_ylabel('Azimuth(degree)')     
#     ax[axi].ticklabel_format(useOffset=False, style='plain')
#     ax[axi].legend(loc='best')
#     ax[axi].grid(True)
#     # velocity
#     axi=1
#     ax[axi].plot(t_1, z_sas, label='$SAS$')
#     ax[axi].plot(t_1, z_fwangle, '-x', label='FWangle by SAS')    
#     ax[axi].set_xlabel('Time(sec)') 
#     ax[axi].set_ylabel('SAS(degree)')     
#     ax[axi].ticklabel_format(useOffset=False, style='plain')
#     ax[axi].legend(loc='best')
#     ax[axi].grid(True)
#     # acceleration
#     # axi=2
#     # ax[axi].plot(t_1, x2)
#     # ax[axi].set_xlabel('Time(sec)') 
#     # ax[axi].set_ylabel('Acceleration(m/s^2)')     
#     # ax[axi].ticklabel_format(useOffset=False, style='plain')
#     # ax[axi].legend(loc='best')
#     # ax[axi].grid(True)

    
#     plt.legend(loc='best')
#     plt.show()

###############################
# main 
###############################
def main(root_log_dir, limit_n_files):
    global g_sidx
    global g_eidx


    # total_files = []
    processed_files = []
    # processed_t = []

    vinfo_day_idx = []
    vinfo_day_t= []
    vinfo_day_dfs = []

    getFullLog = 1

    # #################################
    # # 1. read raw data
    # if LOAD_RAW_DATA_FROM_PKL:
    #     try:
    #         ## Load pickle
    #         f_path = os.path.join(root_log_dir, "log_processed.pkl")
    #         with open(f_path,"rb") as fr:
    #             processed_files = pickle.load(fr)
    #             print("- Processed File List (%d)" % len(processed_files))
    #             print(*processed_files, sep='\n')

    #         f_path = os.path.join(root_log_dir, "vinfo_day.pkl")
    #         with open(f_path, "rb") as fr:
    #             vinfo_day_idx, vinfo_day_t, vinfo_day_dfs = pickle.load(fr) 
    #             print("Load Pickel:", len(vinfo_day_idx), len(vinfo_day_t), len(vinfo_day_dfs))           
    #         print("log_processed.pkl loaded")

    #     except:
    #         f_path = os.path.join(root_log_dir, "log_processed.pkl")            
    #         print("ERROR:No file: %s. Skip Loading" % str(f_path))

    ###############################
    # search_new_file entire_file_list
    new_files = search_new_file(root_log_dir, processed_files)    
    # important. file sorting
    new_files.sort()

    nfiles = len(new_files)
    print("Total:%d log files" % (nfiles))

    vtype_prev = ''
    vid_prev = ''
    year_prev = ''
    month_prev = ''
    day_prev = ''
    df_prev = ''
    eIdx = 0
    if limit_n_files == -1:
        limit_n_files = nfiles
    for i_f in range(nfiles):

        if i_f >= limit_n_files:
            break; 
    
        f_full = new_files[i_f]
        print("- Processing Files(%d/%d) - %s" % (i_f, nfiles, f_full))
        processed_f_name, t, df = LogReader.read_one_file(f_full, getFullLog)
        #print(df)

        print("")
        print("LogData Shape:",end="")
        print(df.shape)

        #ShowFigure(df, t, 620, 920)   # only jumping
        #ShowFigure(df, t, 320, 1220)
        if g_eidx == -1:
            eIdx = len(t)-1
        else:
            eIdx = g_eidx
        ShowFigure(df, t, g_sidx, eIdx)   # only jumping

        f_dat, ext = os.path.splitext(f_full)
        #f_xlsx = f_dat + ".xlsx"
        #df.to_excel(f_xlsx)
        f_csv = f_dat + ".csv"
        df.to_csv(f_csv)

        #exit(0)
        continue

    exit(0)

'''
        # filename, dataframe pair
        processed_files.append(processed_f_name)
        # processed_t.append(t)
        # processed_dfs.append(df)

        #terms = f_full.split('\\')
        terms = f_full.split(DIR_SEP)
        # LOGv4-vt00-id00-2021_10_06
        days = terms[-2].split('-')[-1]     # 2021_10_06
        year, month, day = days.split('_')  # string, 2021, 10, 06

        id_time = terms[-1].split('-')     # vt00-id00-10h_35m_19s-X000000-Y000000.idx
        vtype, vid = id_time[0], id_time[1]
        hh, mm, sec = id_time[2].split('_')      # string

        info_curr = (vtype, vid, year, month, day)
        info_prev = (vtype_prev, vid_prev, year_prev, month_prev, day_prev)

        # append data for each day
        if info_curr in vinfo_day_idx:
            idx = vinfo_day_idx.index(info_curr)
            df_prev = vinfo_day_dfs[idx]
            t_prev = vinfo_day_t[idx]
            #print(len(t_prev), df_prev.shape)
            
            # ignore_index 가 없으면 다시 0부터 시작함
            vinfo_day_dfs[idx] = pd.concat([df_prev, df], ignore_index=True)
            vinfo_day_t[idx].extend(t)
            #print(len(vinfo_day_t), vinfo_day_dfs[idx].shape)

            #plt.figure(str(vinfo_day_idx[idx]))
            #plt.plot(vinfo_day_t[idx])
            #plt.show()

        else:
            vinfo_day_idx.append(info_curr)
            vinfo_day_t.append(t)
            vinfo_day_dfs.append(df)

        #print(days, times)
        # auto save pkl
        if i_f > 0 and i_f % 200 == 0:
            print("SAVE pkl - intermediate (%d/%d)" % (i_f, nfiles))
            if SAVE_RAW_DATA_TO_PKL:
                try:
                    f_path = os.path.join(root_log_dir, "log_processed.pkl")            
                    with open(f_path,"wb") as fw:
                        pickle.dump(processed_files, fw)

                    f_path = os.path.join(root_log_dir, "vinfo_day.pkl")            
                    with open(f_path,"wb") as fw:
                        data = [vinfo_day_idx, vinfo_day_t, vinfo_day_dfs]
                        print("Dump:vinfo_day:", len(vinfo_day_idx), len(vinfo_day_t), len(vinfo_day_dfs))
                        pickle.dump(data, fw)
                except Exception as e:
                    print("Error:", e)
                    print("Saving pickle to current dir:", os.getcwd())
                    f_path = os.path.join(os.getcwd(), "log_processed.pkl")            
                    with open(f_path,"wb") as fw:
                        pickle.dump(processed_files, fw)

                    f_path = os.path.join(os.getcwd(), "vinfo_day.pkl")            
                    with open(f_path,"wb") as fw:
                        data = [vinfo_day_idx, vinfo_day_t, vinfo_day_dfs]
                        print("Dump:vinfo_day:", len(vinfo_day_idx), len(vinfo_day_t), len(vinfo_day_dfs))
                        pickle.dump(data, fw)

    if SAVE_RAW_DATA_TO_PKL and nfiles > 0:
        print("SAVE pkl- final (%d/%d)" % (i_f, nfiles))
        try:
            f_path = os.path.join(root_log_dir, "log_processed.pkl")            
            with open(f_path,"wb") as fw:
                pickle.dump(processed_files, fw)

            f_path = os.path.join(root_log_dir, "vinfo_day.pkl")            
            with open(f_path,"wb") as fw:
                data = [vinfo_day_idx, vinfo_day_t, vinfo_day_dfs]
                print("Dump:vinfo_day:", len(vinfo_day_idx), len(vinfo_day_t), len(vinfo_day_dfs))
                pickle.dump(data, fw)
        except Exception as e:
            print("Error:", e)
            print("Skip saving picle to current dir:", os.getcwd())
            f_path = os.path.join(os.getcwd(), "log_processed.pkl")            
            with open(f_path,"wb") as fw:
                pickle.dump(processed_files, fw)

            f_path = os.path.join(os.getcwd(), "vinfo_day.pkl")            
            with open(f_path,"wb") as fw:
                data = [vinfo_day_idx, vinfo_day_t, vinfo_day_dfs]
                print("Dump:vinfo_day:", len(vinfo_day_idx), len(vinfo_day_t), len(vinfo_day_dfs))
                pickle.dump(data, fw)

    #################################
    # 2. Calculate all_automode
    # No append allowed. Just Load or Calculate all
    sum_vinfo_all_automode = []
    if LOAD_ALL_AUTOMODE_FROM_PKL:
        print("SKIP: Calculate all automode. Load from pkl ")
        f_path = os.path.join(root_log_dir, "sum_vinfo_all_automode.pkl")        
        try:
            with open(f_path,"rb") as fr:
                sum_vinfo_all_automode = pickle.load(fr)
            print("Load sum_vinfo_all_automode: ", len(sum_vinfo_all_automode))
        except:
            print("ERROR: no file: %s. SKIP " % str(f_path))
    else:
        print("- Calculate all automode ")
        for i in range(len(vinfo_day_idx)):
            # plt.plot(processed_dfs[i].iloc[:,0])
            # plt.show()
            print(vinfo_day_idx[i])
            res = process_one_day(vinfo_day_idx[i], vinfo_day_t[i], vinfo_day_dfs[i])
            sum_vinfo_all_automode.append(res)

        if SAVE_ALL_AUTOMODE_TO_PKL:
            try:
                f_path = os.path.join(root_log_dir, "sum_vinfo_all_automode.pkl")            
                with open(f_path,"wb") as fw:
                    pickle.dump(sum_vinfo_all_automode, fw)
                    print("Dump:sum_vinfo_all_automode:", len(sum_vinfo_all_automode))            
            except Exception as e:
                print("Error:", e)
                print("Save dump to current dir:", os.getcwd())
                f_path = os.path.join(os.getcwd(), "sum_vinfo_all_automode.pkl")            
                with open(f_path,"wb") as fw:
                    pickle.dump(sum_vinfo_all_automode, fw)
                    print("Dump:sum_vinfo_all_automode:", len(sum_vinfo_all_automode))            

    # print("- Processed File List (%d)" % len(processed_files))
    # print(*processed_files, sep='\n')
    # print(*vinfo_day_idx, sep='\n')

    print("- All Auto Mode Results: ")
    print("(vinfo, t_start, t_end, loc_start, loc_end, clusterNo, idx_s, idx_e, reason_mode, distance)")
    #for i in range(len(sum_vinfo_all_automode)):
    #        print(*sum_vinfo_all_automode[i], sep='\n')

    #################################
    # 3. Summary the results
    ##############################
    # 날짜별 주행거리 합산
    dist_day = 0
    sum_vinfo_idx = []
    sum_vinfo_day = []
    for i in range(len(sum_vinfo_all_automode)):
        res = sum_vinfo_all_automode[i]
        vinfo_day = res[0][0]
        sum_vinfo_idx.append(vinfo_day)     # vinfo_day
        dist_day = 0
        for j in range(len(res)):
            dist_day += res[j][9] 
        sum_vinfo_day.append([vinfo_day, dist_day/1000])

    sum_vinfo_day.sort()

    print("- Result per Day(km)")
    print(*sum_vinfo_day, sep='\n')

    ##############################
    # 월별 주행거리 합산
    vinfo_month_prev = []
    dist_month = [] 
    sum_vinfo_month = []
    for i in range(len(sum_vinfo_day)):
        sum_vinfo = sum_vinfo_day[i]
        vinfo_month = sum_vinfo[0][0:-1]
        dist = sum_vinfo[1]
        try:
            idx = vinfo_month_prev.index(vinfo_month)
            dist_month[idx] += dist
        except:
            #no index
            #print("Add new vinfo_month", vinfo_month)
            vinfo_month_prev.append(vinfo_month)
            dist_month.append(dist)

    for i in range(len(vinfo_month_prev)):
        # append the final month
        sum_vinfo_month.append([vinfo_month_prev[i], dist_month[i]])

    sum_vinfo_month.sort()

    print("- Result per Month(km)")
    print(*sum_vinfo_month, sep='\n')

    ##############################
    # 반기별, 전체 주행거리 합산
    # ('vt10', 'id01', '2021', '09') --> ('vt10', 'id01', '2021')
    #vinfo_year_prev = sum_vinfo_month[0][0][0:-1]
    vinfo_year_prev = []
    dist_1st_half = []
    dist_2nd_half = []
    dist_year = []
    sum_vinfo_year = []
    for i in range(len(sum_vinfo_month)):
        sum_vinfo = sum_vinfo_month[i]
        vinfo_year = sum_vinfo[0][0:3]     # ('vt10', 'id01', '2021')
        vinfo_month = sum_vinfo[0][3]
        month = int(vinfo_month)
        dist = sum_vinfo[1]
        try:
            idx = vinfo_year_prev.index(vinfo_year)
            dist_year[idx] += dist
            if month <= 6:
                dist_1st_half[idx] += dist
            else:
                dist_2nd_half[idx] += dist
        except:
            vinfo_year_prev.append(vinfo_year)
            dist_year.append(dist)
            if month <= 6:
                dist_1st_half.append(dist)
                dist_2nd_half.append(0)
            else:
                dist_1st_half.append(0)
                dist_2nd_half.append(dist)

    for i in range(len(vinfo_year_prev)):
        # append the final month
        sum_vinfo_year.append([vinfo_year_prev[i], dist_1st_half[i], dist_2nd_half[i], dist_year[i]])
            
    sum_vinfo_year.sort()

    print("- Result per Year(km): 1st half, 2nd half, full year")
    print(*sum_vinfo_year, sep='\n')

    ##########################
    # 4. 결과 txt로 저장
    now = datetime.datetime.now()
    nowDate = now.strftime('%Y_%m_%d')      # 2021-04-19
    nowTime = now.strftime('%H:%M:%S')      # 12h-11m-21s
    print(nowTime)      # 12:11:32

    try:
        f_result = os.path.join(root_log_dir, 'result_'+nowDate+'.txt')      
        with open(f_result, "w") as f:
        #f.write(*sum_vinfo_year, sep='\n')

            f.write("- Result per Year(km): 1st half, 2nd half, full year\n")        
            result = '\n'.join(str(s) for s in sum_vinfo_year)
            f.write(result)
            f.write("\n")

            f.write("- Result per Month(km)\n")
            result = '\n'.join(str(s) for s in sum_vinfo_month)
            f.write(result)
            f.write("\n")

            f.write("- Result per Day(km)\n")
            result = '\n'.join(str(s) for s in sum_vinfo_day)
            f.write(result)
            f.write("\n")    
    except Exception as e:
        print("Error:", e)
        print("Save result file to current dir:", os.getcwd())
        f_result = os.path.join(os.getcwd(), 'result_'+nowDate+'.txt')      
        with open(f_result, "w") as f:
        #f.write(*sum_vinfo_year, sep='\n')

            f.write("- Result per Year(km): 1st half, 2nd half, full year\n")        
            result = '\n'.join(str(s) for s in sum_vinfo_year)
            f.write(result)
            f.write("\n")

            f.write("- Result per Month(km)\n")
            result = '\n'.join(str(s) for s in sum_vinfo_month)
            f.write(result)
            f.write("\n")

            f.write("- Result per Day(km)\n")
            result = '\n'.join(str(s) for s in sum_vinfo_day)
            f.write(result)
            f.write("\n")    
'''

from io import StringIO
import io
from urllib.request import urlopen  

def test():
    url = "http://maps.googleapis.com/maps/api/staticmap?center=-30.027489,-51.229248&size=800x800&zoom=14&sensor=false"
    # im = Image.open(cStringIO.StringIO(urllib2.urlopen(url).read()))
    im = Image.open(io.BytesIO(urlopen(url).read()))
    plt.imshow(im)
    plt.show()
    exit()

def test2():
    import matplotlib.pyplot as plt
    from shapely.geometry import Point
    import geopandas as gpd
    import pandas as pd
    import contextily as cx

    # Let's define our raw data, whose epsg is 4326
    df = pd.DataFrame({
        'LAT'  :[-22.266415, -20.684157],
        'LONG' :[166.452764, 164.956089],
    })
    df['coords'] = list(zip(df.LONG, df.LAT))

    # ... turn them into geodataframe, and convert our
    # epsg into 3857, since web map tiles are typically
    # provided as such.
    geo_df = gpd.GeoDataFrame(
        df, crs  ={'init': 'epsg:4326'},
        geometry = df['coords'].apply(Point)
    ).to_crs(epsg=3857)

    # ... and make the plot
    ax = geo_df.plot(
        figsize= (5, 5),
        alpha  = 1
    )
    cx.add_basemap(ax, zoom=10)
    ax.set_axis_off()
    plt.title('Kaledonia : From Hienghène to Nouméa')
    plt.show()
    exit()

# 로그데이터 로딩 자체에 시간이 많이 걸리고, 계산에는 얼마 걸리지 않음. 
# 그래서 한번 로딩한 것은 피클로 저장해서 다시 로드해서 사용
# 계산은 각 날짜에 다시 추가되는 것이 있으므로, 
# 처음부터 다시 계산하던지, 아니면 아예 로드해서(추가없이) 사용할 것
LOAD_RAW_DATA_FROM_PKL = 1
LOAD_ALL_AUTOMODE_FROM_PKL = 0      # No append allowed. Just Load or Calculate all
SAVE_RAW_DATA_TO_PKL = 0
SAVE_ALL_AUTOMODE_TO_PKL = 0

SKIP_VIRTUAL_VEHICLE = 1
SHOW_PLOT = 0

g_sidx = 0
g_eidx = -1
# if __name__ == '__main__':


#     #test()
#     test2()


#     # r"string": python raw string
#     # root_log_dir = r"E:\AVP_LOG_dmz_20220110"
#     # root_log_dir = r"E:\DATA\ETRI_LOG\20220420\20220420_EVCU\LOGv4-vt10-id01-2022_04_20"
#     # root_log_dir = r"D:\10_Project\DATA\LOGv4-vt10-id01-2022_04_20"
#     #root_log_dir = r"E:\AVP_LOG_dmz_20220110"

#     #root_log_dir = r"E:\DATA\ETRI_LOG\20220420\20220420_EVCU\LOGv4-vt10-id01-2022_04_20"
#     #root_log_dir = r"E:\Data\LOGv4-vt10-id01-2022_04_20-manual2"
#     # root_log_dir = r"D:\home\etri01\TEMP-06\LOGv4-vt10-id00-2022_07_01"
#     # root_log_dir = r"D:\home\etri01\sda1\AVP_LOG\VT40-ID00\LOGv4-vt40-id00-2022_05_11"
#     #root_log_dir = r"E:\DATA\ETRI_LOG\20220420\20220420_EVCU\LOGv4-vt10-id01-2022_04_20"
#     # root_log_dir = r"E:\Data\VT20-ID02\LOGv4-vt20-id02-2022_05_30"
#     # gangneung
#     #root_log_dir = r"D:\home\etri01\AVP_LOG\LOGv4-vt40-id01-2023_02_01"
#     root_log_dir = ROOT_LOG_DIR

#     limit_n_files = -1   # max number of new files. -1:max, 0:no new file
#     # limit_n_files = 3   # max number of new files. -1:max, 0:no new file
#     main(root_log_dir, limit_n_files)

