import os
import sys

import numpy as np

# matplotlib.use('Qt5Agg')
# from PySide6.QtWidgets import QMainWindow, QApplication

from PySide6.QtWidgets import *
# ref: https://www.pythonguis.com/faq/pyqt6-vs-pyside6/
from PySide6.QtCore import Signal, Slot # PySide6: Signal, Slot, PyQt6: pyqtSignal, pyqtSlot
from PySide6.QtCore import QTimer

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import LogReader
import Utils


import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import pyqtgraph as pg

from threading import Lock, Thread


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self):
        fig = Figure()
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


    def draw_graph_1d(self, t, xs, xs_label):
        self.axes.cla()
        # self.sc_1d.axes.plot(t, xs, t, xs2, color = 'blue', lw = 1)
        self.axes.plot(t, xs)
        # self.axes.set_xlabel("x")
        self.axes.set_ylabel(xs_label)
        self.axes.grid()
        self.draw()

    def draw_graph_add(self, t, xs):
        self.axes.plot(t, xs)
        self.draw()


class C_wLocation(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)  # Ui_wLocation

        self.wdg_Location.setTitle('Location-Full')
        self.wdg_Location.setBackground('b')
        self.wdg_Location.setLabel('left', 'Latitude(m)')
        self.wdg_Location.setLabel('bottom', 'Longitude(m)')
        self.wdg_Location.addLegend()
        self.wdg_Location.showGrid(x=True, y=True)

    def ShowFigure(self, z_long, z_lati):
        self.wdg_Location.plot(z_long, z_lati)

class MplWidget(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.sc_1d = MplCanvas()
        toolbar = NavigationToolbar(self.sc_1d, self)

        layout = QVBoxLayout()

        layout.addWidget(toolbar)
        layout.addWidget(self.sc_1d)

        self.setLayout(layout)
        self.show()

    def draw_graph_1d(self, t, xs, xs_label=""):
        self.sc_1d.axes.cla()
        # self.sc_1d.axes.plot(t, xs, t, xs2, color = 'blue', lw = 1)
        self.sc_1d.axes.plot(t, xs)
        # self.sc_1d.axes.set_xlabel("x")
        self.sc_1d.axes.set_ylabel(xs_label)
        self.sc_1d.axes.grid()
        self.sc_1d.draw()

    def draw_graph_1d2(self, t, xs, xs2):
        self.sc_1d.axes.cla()
        # self.sc_1d.axes.plot(t, xs, t, xs2, color = 'blue', lw = 1)
        self.sc_1d.axes.plot(t, xs, t, xs2)
        # self.sc_1d.axes.set_xlabel("x")
        #self.sc_1d.axes.set_ylabel("y")
        self.sc_1d.axes.grid()
        self.sc_1d.draw()

    def draw_graph_add(self, t, xs):
        self.sc_1d.axes.plot(t, xs)
        self.sc_1d.draw()


class Main(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.sc_2d = MplCanvas()
        # self.sc_1d = MplCanvas()
        self.draw_graph_2d([0], [0])
        # self.draw_graph_1d([0])
        toolbar = NavigationToolbar(self.sc_2d, self)

        layout = QVBoxLayout()

        layout.addWidget(toolbar)
        layout.addWidget(self.sc_2d)

        self.setLayout(layout)
        self.show()

    def draw_graph_2d(self, xs, ys):
        # xs = np.linspace(0, 1, 101)
        # ys = xs**2.0
        self.sc_2d.axes.cla()
        self.sc_2d.axes.plot(xs, ys, color = 'blue', lw = 1)
        self.sc_2d.axes.set_xlabel("x")
        self.sc_2d.axes.set_ylabel("y")
        self.sc_2d.axes.grid()
        self.sc_2d.draw()

class SimWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):

        self.canvas_s = MplCanvas()
        # self.sc_1d = MplCanvas()
        # self.draw_graph_2d([0], [0])
        # # self.draw_graph_1d([0])
        # toolbar = NavigationToolbar(self.sc_2d, self)

        self.canvas_v = MplCanvas()
        # self.canvas_a = MplCanvas()


        # button 'ACC simulation window'
        self.btn_sim = QPushButton(text="Start Simulation")
        self.btn_sim.clicked.connect(self.btn_clicked_start_sim)    


        layout = QVBoxLayout()

        # layout.addWidget(toolbar)
        layout.addWidget(self.canvas_s)
        layout.addWidget(self.canvas_v)
        layout.addWidget(self.btn_sim)

        self.setLayout(layout)
        self.show()

  

    def btn_clicked_start_sim(self):
        obj_start_pos_x = 0
        obj_vel_kph = 0
        obj_accel_mps = 0

        s = obj_start_pos_x
        v = obj_vel_kph / 3.6   # kph --> mps
        a = obj_accel_mps

        t_range = list(range(0, 10))
        f_s = []
        f_v = []
        f_a = []
        for t in t_range:
            obj_s = s + v*t + 0.5*a*t^2
            obj_v = v + a*t
            obj_a = a

            f_s.append(obj_s)
            f_v.append(obj_v)
            f_a.append(obj_a)

        self.canvas_s.draw_graph_1d(t_range, f_s, "Position")
        self.canvas_v.draw_graph_1d(t_range, f_v, "Velocity")
        



class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()


        layout = QHBoxLayout()

        l_layout = QVBoxLayout()
        r_layout = QVBoxLayout()

        layout.addLayout(l_layout)
        layout.addLayout(r_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.graph_2d = Main()
        self.input = QTextEdit()        
        self.listWidget_dir = QListWidget()


        # label 'File to process'
        self.label_sel_file = QLabel('File to process', self)
        font_dir = self.label_sel_file.font()
        font_dir.setPointSize(12)
        font_dir.setFamily('Times New Roman')
        font_dir.setBold(True)
        self.label_sel_file.setFont(font_dir)

        # button 'Select log file'
        self.btn_select_file= QPushButton(text="Select log file")
        self.btn_select_file.clicked.connect(self.btn_select_clicked)

        # button 'Start Processing'
        self.btn_proc = QPushButton(text="Start Processing")
        self.btn_proc.clicked.connect(self.btn_proc_clicked)

        # button 'Convert to CSV'
        self.btn_convert_to_csv = QPushButton(text="Convert to csv")
        self.btn_convert_to_csv.clicked.connect(self.btn_clicked_convert_to_csv)

        # button 'ACC simulation window'
        self.btn_sim = QPushButton(text="ACC simulation")
        self.btn_sim.clicked.connect(self.btn_clicked_sim)        

        # # label 'Select Data Folder'
        # self.label_sel_folder = QLabel('Select data folder', self)
        # font_dir = self.label_sel_folder.font()
        # font_dir.setPointSize(12)
        # font_dir.setFamily('Times New Roman')
        # font_dir.setBold(True)
        # self.label_sel_folder.setFont(font_dir)

        # plain text edit
        self.edit_sel_file = QTextEdit()
        # fname = r"C:\Git\AVP_LOG\2023_07\VT50_ID01\vt50-id51-2023_07_26\vt50-id51-07_26-17h_33m_07s-X179895-Y515630.idx"
        # fname = r"D:\20_Data\VT50-ID51\vt50-id51-2023_08_09\17h_36m_38s-X37.244750-Y126.775284.idx"
        fname = r"D:\20_Data\VT50-ID51\vt50-id51-2023_08_09\17h_26m_38s-X37.243925-Y126.775314.idx"
        fname = r"E:/AVP_LOG/AVP_LOG_carnival_20230814/2023_08/VT40-ID01/vt40-id01-2023_08_14/vt40-id01-08_14-10h_21m_08s-X232666-Y417859.idx"

        self.edit_sel_file.setPlainText(fname)

        ly_sel_file = QVBoxLayout()
        ly_sel_file.addWidget(self.label_sel_file)

        ly_2btns = QHBoxLayout()
        ly_2btns.addWidget(self.btn_select_file)
        ly_2btns.addWidget(self.btn_proc)
        ly_2btns.addWidget(self.btn_convert_to_csv)
        ly_2btns.addWidget(self.btn_sim)
        cont_1 = QWidget()
        cont_1.setLayout(ly_2btns)
        ly_sel_file.addWidget(cont_1)
        ly_sel_file.addWidget(self.edit_sel_file)

        # self.textFolderName = QTextEdit()
        # dname = r"E:\AVP_LOG\AVP_LOG_tmp\VT50-ID51\LOGv4-vt50-id51-2023_07_11"
        # self.textFolderName.setPlainText(dname)
        # ly_sel_file.addWidget(self.textFolderName)


        # add all widgets
        l_layout.addWidget(self.graph_2d)
        # l_layout.addWidget(self.input)

        # l_layout.addWidget(self.label_dir)
        # l_layout.addWidget(self.plainTextEdit)
        # l_layout.addWidget(self.btn_proc)

        # l_layout.addWidget(self.textFolderName)
        container_mid = QWidget()
        container_mid.setLayout(ly_sel_file)
        l_layout.addWidget(container_mid)

        self.graph_mode = MplWidget()
        self.graph_1d = MplWidget()
        self.graph_canvas = MplWidget()
        self.graph_3 = MplWidget()
        r_layout.addWidget(self.graph_mode)
        r_layout.addWidget(self.graph_1d)
        r_layout.addWidget(self.graph_canvas)
        r_layout.addWidget(self.graph_3)

        self.listWidget_dir.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # child window variable
        self.child_windows = []

    def btn_clicked_sim(self):
        # sim_window = QDialog()
        sim_window = Main()
        self.child_windows.append(sim_window)
        sim_window.show()

    def btn_select_clicked(self):
        filter = "Index Files (*.idx);;Text Files (*.txt);;All Files (*)"
        fnames, _ = QFileDialog.getOpenFileNames(self, "Select files", "", filter)
        print(fnames)
        edit_names = ""
        for fname in fnames:
            edit_names += fname + "\n"
        self.edit_sel_file.setPlainText(edit_names)

    def btn_clicked_convert_to_csv(self):
        fname_raw = self.edit_sel_file.toPlainText()

        fnames = fname_raw.split()
        print("fname:", fnames)

        for fname in fnames:
            getFullLog = 1
            processed_f_name, t, df = LogReader.read_one_file(fname, getFullLog)
            print("df:", df.shape)

            f = os.path.splitext(fname)

            fname_csv = f[0] + ".csv"
            print(fname_csv)

            df.to_csv(fname_csv, sep=',')


        # g_sidx = 0
        # eIdx = len(t)-1

        # l_sas_bias = df.iloc[g_sidx:eIdx, 121].to_list()    # 121: sas_bias

        # print("sas_bias:", l_sas_bias[-1])
        # z_long, z_lati = self.ShowFigure(df, t, g_sidx, eIdx)

    def btn_proc_clicked(self):
        fname = self.edit_sel_file.toPlainText()

        # self.wLocation = C_wLocation()
        # # 새로 생성한 윈도우 관리를 위해 변수사용
        # # https://martinii.fun/158
        # self.child_windows.append(self.wLocation)
        # # setupUi가 호출되는 창의 ui가 변경됨
        # # setupUi를 여기서 호출하면 이 윈도우 Ui가 변경됨. 
        # # 그러므로 여기서 self.wLocation.setupUi로 호출하면 안되고, 
        # # 새로 생성된 창에서 setupUi가 호출되도록 해야 함
        # #self.wLocation.setupUi(self)   
        # # C_wLocation()객체 생성후, show()만 하면 창이 생성됨
        # self.wLocation.show()


        #print("- Processing Files(%d/%d) - %s" % (i_f, nfiles, f_full))
        getFullLog = 1
        processed_f_name, t, df = LogReader.read_one_file(fname, getFullLog)
        print("df:", df.shape)

        g_sidx = 0
        eIdx = len(t)-1

        l_sas_bias = df.iloc[g_sidx:eIdx, 121].to_list()    # 121: sas_bias

        print("sas_bias:", l_sas_bias[-1])
        z_long, z_lati = self.ShowFigure(df, t, g_sidx, eIdx)
        # self.ShowFigure_Location(z_long, z_lati)
        # self.wLocation.ShowFigure(z_long, z_lati)

    def ShowFigure(self, df, t_all, idx_s, idx_e):
        t = t_all[idx_s: idx_e]

        col_t = 4
        col_mode = 5
        col_reasomMode = 6

        col_vislong = 15
        col_vislati = 16
        col_velocity= 18
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
        col_invehi_sas = 57
        col_obj_rel_dist2 = 49
        col_obj_rel_vel2 = 50
        col_lati = 22
        col_heading = 26


        col_long_gps = 21
        col_lati_gps = 22
        col_azi_gps = 26

        col_fin_cmd_sas = 105

        mode = df.iloc[idx_s:idx_e, col_mode].to_list()
        reason_mode = df.iloc[idx_s:idx_e, col_reasomMode].to_list()
        invehi_sas = df.iloc[idx_s:idx_e, col_invehi_sas].to_list()
        fin_cmd_sas = df.iloc[idx_s:idx_e, col_fin_cmd_sas].to_list()

        velocity = df.iloc[idx_s:idx_e, col_velocity].to_list()
        obj_rel_dist = df.iloc[idx_s:idx_e, col_obj_rel_dist2].to_list()
        obj_rel_dist = list(map(lambda x:(x/10.0), obj_rel_dist))
        obj_rel_vel = df.iloc[idx_s:idx_e, col_obj_rel_vel2].to_list()
     


        z_long = df.iloc[idx_s:idx_e, col_vislong].to_list()
        z_lati = df.iloc[idx_s:idx_e, col_vislati].to_list()

        x_est= df.iloc[idx_s:idx_e, col_x_est].to_list()
        y_est = df.iloc[idx_s:idx_e, col_y_est].to_list()

        long_gps = df.iloc[idx_s:idx_e, col_long_gps].to_list()
        lati_gps = df.iloc[idx_s:idx_e, col_lati_gps].to_list()

        # straight line, from start to end
        long_1 = [z_long[0], z_long[-1]]
        lati_1 = [z_lati[0], z_lati[-1]]

        a,b,c = Utils.getLine((z_long[0], z_lati[0]), (z_long[-1], z_lati[-1]))
        d_list = []
        for lo, li in zip(z_long, z_lati):
            d = Utils.getDistwLine((lo,li), a, b, c)
            d_list.append(d)

        azi_list = []
        lo_0, li_0 = z_long[0], z_lati[0]
        azi_default = Utils.getAzimuth((lo_0, li_0), (z_long[-1], z_lati[-1]))
        d_tic = 100
        for i, (lo, li) in enumerate(zip(z_long, z_lati)):
            if i < d_tic:
                a = azi_default
            else:
                prev = i-d_tic
                a = Utils.getAzimuth((z_long[prev], z_lati[prev]), (lo, li))
            azi_list.append(a)

        azi_list_10 = []
        lo_0, li_0 = z_long[0], z_lati[0]
        azi_default = Utils.getAzimuth((lo_0, li_0), (z_long[-1], z_lati[-1]))
        d_tic = 50
        for i, (lo, li) in enumerate(zip(z_long, z_lati)):
            if i < d_tic:
                a = azi_default
            else:
                prev = i-d_tic
                a = Utils.getAzimuth((z_long[prev], z_lati[prev]), (lo, li))
            azi_list_10.append(a)

        ###############################
        # figure 1: Location
        # self.graphWidget.plot(hour, temperature)
        # ax.plot(z_long, z_lati, '-o', label='Measured', linewidth=1.0)
        # ax.plot(x_est, y_est, '-x',  label='Predicted', linewidth=1.0)
        # ax.plot(long_1, lati_1, '-x',  label='Measured', linewidth=1.0)
        # self.graphWidget.plot(z_long, z_lati)
        self.graph_2d.draw_graph_2d(z_long, z_lati)
        self.graph_mode.draw_graph_1d(t_1, mode)
        self.graph_1d.draw_graph_1d2(t_1, invehi_sas, fin_cmd_sas)
        self.graph_canvas.draw_graph_1d(t_1, velocity, 'Velocity')
        self.graph_3.draw_graph_1d(t_1, velocity, 'Velocity')
        self.graph_3.draw_graph_add(t_1, obj_rel_dist)
        self.graph_3.draw_graph_add(t_1, obj_rel_vel)

        return z_long, z_lati
    #     self.button = QPushButton(parent=self)
    #     self.setCentralWidget(self.button)
    #     self.button.setCheckable(True)
    #     self.button.clicked.connect(self.button_clicked)
    #     self.click_count = 0
 
    # def button_clicked(self):
    #     self.click_count += 1
    #     self.button.setText(f"{self.click_count}번 클릭함")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())   # app.exec_() also OK.