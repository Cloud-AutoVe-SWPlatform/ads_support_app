import os
import sys

import struct
import numpy as np
import pandas as pd
#from matplotlib import pyplot as plt
import matplotlib.pyplot as plt

# ref: https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html
plt.style.use('bmh')


import pickle
import datetime

# # sys.path에 상위 디렉토리 추가
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
# #print(sys.path)

# https://jhryu1208.github.io/devlang/2020/11/17/dirimport/
# https://www.delftstack.com/ko/howto/python/python-import-from-parent-directory/
from LogFormat import LogFormat101
from LogFormat import LogFormat449
from LogFormat import LogFormat410
from LogFormat import LogFormat500
from LogFormat import LogFormat501
from LogFormat import LogFormat510
from LogFormat import LogFormat512
from LogFormat import LogFormat5122
from LogFormat import LogFormat601

import LogReporter

def read_one_file(f_idx_name, getFull, sidx, ilen):

    # get year, month, day
    info_curr = LogReporter.get_info_curr(f_idx_name)
    #c_year, c_month, c_day = info_curr[2], info_curr[3], info_curr[4]

    f_dat_name = f_idx_name[:-4] + ".dat"
    #print("f_dat:", f_dat_name)

    df = pd.DataFrame()

    # f_idx: log_time(u32), log_start_idx(u32), log_len(u32)
    try:
        f_idx = open(f_idx_name, "rb")
        f_idx_buf = f_idx.read()
        f_idx.close()
    except Exception as e:
        print("Error:No idx file:",f_idx_name, e)
        print("Skip the file")
        t = []
        return f_idx_name, t, df, info_curr


    f_idx_len = len(f_idx_buf)
    # print("f_idx_len:", f_idx_len, "items:", f_idx_len/12)     # 12bytes per index

    if f_idx_len == 0:
        print("NoDATA:", f_idx_name)
        # no data
        # return None
        t = []
        return f_idx_name, t, df, info_curr

    try:
        f_dat = open(f_dat_name, "rb")
        f_dat_buf = f_dat.read()    
        f_dat.close()
    except Exception as e:
        print("Error:No idx file:",f_idx_name, e)
        print("Skip the file")
        t = []
        return f_idx_name, t, df, info_curr


    n_items = int(len(f_idx_buf)/12)

    if ilen == 0:
        ilen = n_items
    if (sidx+ilen) > n_items:
        ilen = n_items - sidx

    times = [0] * ilen
    # year = [c_year] * ilen      # type: list[str]
    # month = [c_month] * ilen    # str
    # day = [c_day] * ilen        # str

    log101 = LogFormat101.D_LOG_FORMAT()
    log449 = LogFormat449.D_LOG_FORMAT()
    log410 = LogFormat410.D_LOG_FORMAT()    
    log500 = LogFormat500.D_LOG_FORMAT()
    log501 = LogFormat501.D_LOG_FORMAT()
    log510 = LogFormat510.D_LOG_FORMAT()    
    log512 = LogFormat512.D_LOG_FORMAT()    
    log5122 = LogFormat5122.D_LOG_FORMAT()
    log601 = LogFormat601.D_LOG_FORMAT()
    #print("f_idx:", f_idx_name)

    logs = []
    log = None
    nFields = 0
    eidx = sidx+ilen
    for i in range(sidx, eidx):
    #for i in range(10):

        s_i = i*12 
        log_time, log_start_idx, log_len = struct.unpack("<III", f_idx_buf[s_i:s_i+12])
        # if i % 100 == 0:
        #     # print '\r' : move cursor to the fisrt. In python use with end='' option
        #     print("(%d/%d)time:%d, start:%d, len:%d \r" % (i, n_items, log_time, log_start_idx, log_len), end='')
        #     # print("(%d/%d)time:%d, start:%d, len:%d \n" % (i, n_items, log_time, log_start_idx, log_len), end='')

        #print("(%d/%d)time:%d, start:%d, len:%d \r" % (i, n_items, log_time, log_start_idx, log_len), end='')


        #log_one_line = f_dat_buf[log_start_idx: log_start_idx+log_len]

        #log_version, vtype, vid = struct.unpack("<HHH", log_one_line[0:6])
        #log_version, vtype, vid, _, _, _ = struct.unpack("<6B", log_one_line[0:6])
        #print("log_len:", log_len)
        log_version, vtype, vid = struct.unpack("<BBB", f_dat_buf[0:3])
        # print('log_version:', log_version, end='\n')

        dummy_head = b''
        dummy_tail = b''

        if log_version == 60:
            if log_len == 400:
                log = log601

        if log_version == 164:
            if log_len == 80:
                log = log101
            elif log_len == 76:
                dummy_head = struct.pack('<4B', 0,0,0,0)
                log = log101

        # old school
        if log_len == 667:
            log = log410
        elif log_len == 413:
            log = log510
        elif log_len == 428:
            log = log501
        elif log_len == 405 and log_version == 254:
            log = log510
            dummy_tail = struct.pack('<8B', 0,0,0,0,0,0,0,0)
        elif log_len == 396:
            log = log601
            # log vt50-id51-2023_09_05
            dummy_head = struct.pack('<4B', 60, 50, 51, 0)
        elif log_len == 76:
            log = log101
            dummy_head = struct.pack('<4B', 0, 0, 0, 0)

        elif log_len == 480:
            log = log512
        elif log_len == 464:
            log = log5122

        if log == None:
            print("ERROR: log object: ",f_idx_name)
            print('ERROR: log_v:%d, log_len:%d - %02x,%02x' % (log_version, log_len, f_dat_buf[0], f_dat_buf[1]), end='\n')
            continue

        # if log_len == 667:
        #     log = log410
        # elif log_len == 449:
        #     log = log449
        # elif log_len == 319:
        #     log = log501
        # elif log_len == 413:
        #     log = log510
        # elif log_len == 464:
        #     log = log5122
        # elif log_len == 480 or log_len==464:
        #     log = log512
        #     # fmf_size = log.getsize()
        #     # print("fmf_size:", fmf_size)
        # else:
        #     #print("ERROR: log_len(%d) is not matched. Use default" % log_len)
        #     log = log601

        try:
            # # Unpack: time, mode, reason_mode, long, lati, heading
            # log_version = f_dat_buf[0]
            # if log_version == 60:
            #     oneLine = log.Unpack(f_dat_buf[log_start_idx: log_start_idx+log_len])
            # else:
            #     dummy = struct.pack('<BBBB', 0,0,0,0)
            #     oneLine = log.Unpack(dummy+f_dat_buf[log_start_idx: log_start_idx+log_len], getFull)

            oneLine = log.Unpack(dummy_head+f_dat_buf[log_start_idx: log_start_idx+log_len]+dummy_tail, getFull)
                
            nFields = log.nFields
            
        except Exception as e:
            print("")
            print("Error:log.Unpack:", f_idx_name, log_time, log_start_idx, log_len, e)
            if getFull == 0:
                oneLine = [0,0,0,0,0,0]
            else:
                print("")
                print("log.nFields:", log.nFields)
                oneLine = [0] * log.nFields

        times[i] = log_time
        logs.append(oneLine)
        #df = df.append(log.pd_log, ignore_index=True)
        #print(df)
    # if getFull == 0:
    #     c_names = ['time', 'mode', 'reason_mode', 'long', 'lati', 'heading', 
    #                 'TargetSAS', 'SAS_FD', 'APS', 'BPS', 'GearPos']
    #     df = pd.DataFrame(logs, columns=c_names)        
    # else:
    #     #print(c_names)
    #     #print("nFields:", nFields)
    #     c_names = list(map(str, range(nFields)))
    #     #print(c_names)
    #     # c_names[0:5] = ['LogV', 'vType', 'vId', 'res', 't_mainLoop']
    #     # c_names[5:17] = ['vcuMode', 'reasonMode', 'modeOut', 'modeIn', \
    #     #     'accFdInfo', 'statusLog', 'event1', 'event2', 'errorList1', \
    #     #     'res', 'lppsubType', 'errorList2']
    #     c_names[8] = 'SAS_FD'
    #     c_names[134:136] = ['APS_FD', 'BPS_FD']
    #     c_names[146] = 'TargetSAS'
    #     c_names[179:183] = ['tg_accel_pedal', 'tg_brake_pedal', \
    #                         'tg_gear', 'tg_bcm']

    #     c_names = log.getColumnNames(getFull)

    #     # print(c_names)
    #     df = pd.DataFrame(logs, columns=c_names)
    #print("")

    if log != None:
        c_names = log.getColumnNames(getFull)
        # print(c_names)
        df = pd.DataFrame(logs, columns=c_names)
    else:
        print("Error: logObj None: ", f_idx_name)

    #########################
    # plot draw
    # 11:longitude, 12:latitude

    if SHOW_FIGURE_ONE:
        ShowFigure(df)
        # fig, axs = plt.subplots(2,1)
        # #plt.figure("location")
        # #axs[0].plot(df['long'].to_list(), df.iloc[:,3].to_list())
        # axs[0].plot(df['long'].to_list(), df['lati'].to_list())
        # axs[0].set_xlabel('Longitude')
        # axs[0].set_ylabel('Latitude')
        # axs[0].grid(True)

        # axs[1].plot(df['time'].to_list(), df['mode'].to_list())
        # axs[1].set_xlabel('Times')
        # axs[1].set_ylabel('Mode')        
        # axs[1].grid(True)

        # fig.tight_layout()
        # plt.show()

    # return processed file name
    return f_idx_name, times, df, info_curr

entire_log_files = []
def search_new_file(dirname, processed_files):
    try:
        filenames = os.listdir(dirname)
        for filename in filenames:
            #print(filename.split('-'))
            full_filename = os.path.join(dirname, filename)
            
            if os.path.isdir(full_filename):
                search_new_file(full_filename, processed_files)
            else:
                ext = os.path.splitext(full_filename)[-1]
                if ext == '.idx': 
                    if os.path.getsize(full_filename) == 0:
                        print("File size:0, Skip:", full_filename)
                        continue
                    entire_log_files.append(full_filename)
    except PermissionError:
        pass
    
    #print(vkeyDic)
    return entire_log_files

def hhmmss2sec(t):
    msec = (t/1000.0 - int(t/1000))
    sec  = (t/100000.0 - int(t/100000)) *100
    mm = (t/10000000.0 - int(t/10000000)) *100
    hh = (t/1000000000.0 - int(t/1000000000))*100

    total_sec = hh*3600 + mm*60 + sec + msec
    # print("t:%d - %d:%d:%d:%.03f - %.03f" % (t, hh, mm, sec, msec, total_sec))

    return total_sec


def ShowFigure(df, t_all):

    t = list(range(df.shape[0]))

    fig, axs = plt.subplots(1,1)
    auto_x = df[df['5.evcuMode']==2]['15.pos_x'].to_list()
    auto_y = df[df['5.evcuMode']==2]['16.pos_y'].to_list()
    axs.plot(df['15.pos_x'].to_list(), df['16.pos_y'].to_list(), auto_x, auto_y)
    axs.set_xlabel('Longitude')
    axs.set_ylabel('Latitude')
    axs.grid(True)
    fig.tight_layout()

    fig, axs = plt.subplots(2,1, gridspec_kw={'height_ratios':[2,1]})
    #plt.figure("location")
    auto_x = df[df['5.evcuMode']==2]['15.pos_x'].to_list()
    auto_y = df[df['5.evcuMode']==2]['16.pos_y'].to_list()
    axs[0].plot(df['15.pos_x'].to_list(), df['16.pos_y'].to_list(), auto_x, auto_y)
    axs[0].set_xlabel('Longitude')
    axs[0].set_ylabel('Latitude')
    axs[0].grid(True)
    axs[1].plot(df['4.t_mainLoop'].to_list(), df['5.evcuMode'].to_list())
    axs[1].set_xlabel('Times')
    axs[1].set_ylabel('Mode')        
    axs[1].grid(True)
    fig.tight_layout()

    # plt.figure("heading")
    # plt.plot(df['heading'].to_list())

    # plt.figure("time")
    # plt.plot(df['time'].to_list())

    # plt.figure("SAS")
    fig, ax = plt.subplots()
    # plt.plot(t,df['TargetSAS'].to_list(), t, df['SAS_FD'].to_list())
    ###############
    # time
    base_t = 82900  # 8:29:00 
    t_1 = list(map(lambda x:(x/1000-base_t), t_all))
    # t_1 = list(map(hhmmss2sec, t_all))

    ax.plot(t_1,df['Final_Cmd_SAS'].to_list(), t_1, df['InVehi_SAS'].to_list())

    ax.set_title("Steering control result")
    ax.set_xlabel('Time(sec)') 
    ax.set_ylabel('Steering angle(deg)') 
    ax.grid(True)

    #plt.figure("APS-BPS")
    fig, ax = plt.subplots()
    ###############
    # time
    base_t = 82900
    t_1 = list(map(lambda x:(x/1000-base_t), t_all))
    # t_1 = list(map(hhmmss2sec, t_all))

    ###############
    # target brake
    tg_bps = list(map(lambda x:x/10.0, df['Final_Cmd_pedal_pos_brake'].to_list()))
    # tg_bps = df['Tg_BPS'].to_list()

    ###############
    # brake feedback
    # fd_bps = list(map(lambda x:x*10.0, df['BPS'].to_list()))
    fd_bps = df['InVehi_brake_pressure'].to_list()

    # plt.plot(t, tg_bps, t, fd_bps)
    ax.plot(t_1, tg_bps, t_1, fd_bps)
        # axs[1].set_xlabel('Times')
    ax.set_title("Brake pedal control result")
    ax.set_xlabel('Time(sec)') 
    ax.set_ylabel('Brake push distance(mm)') 
    ax.grid(True)

    plt.show()



SHOW_FIGURE_ONE = 0
SHOW_FIGURE_TOTAL = 1
EXPORT_TO_CSV = 1
if __name__ == '__main__':

    # t = 81527780
    # hhmmss2sec(t)

    # exit(0)


    #f_name = "/media/etri01/T7/AVP_LOG_dmz/VT30-ID06/LOGv4-vt30-id06-2021_09_24/vt30-id06-10h_24m_58s-X000000-Y000000.idx"
    # f_dir = r"E:\AVP_LOG_dmz_20211212\VT10-ID01\LOGv4-vt10-id01-2021_10_20"
    # f_name = r'vt10-id01-11h_16m_13s-X000000-Y000000.idx'
    # #f_name = r'vt10-id01-11h_21m_13s-X000000-Y000000.idx'

    # f_dir = r"E:\AVP_LOG\AVP_LOG_tmp\VT50-ID51"
    f_dir = r"E:\22_AVP_LOG\vt50-id51-2023_08_23"
    
    # f_name = r'vt10-id01-11h_01m_39s-X000000-Y000000.idx'
    #f_name = r'vt10-id01-11h_21m_13s-X000000-Y000000.idx'
    
    f_names = search_new_file(f_dir, [])
    print("LogFiles=")
    print(*f_names, sep='\n')
    print("total files:", len(f_names))

    s_idx = 0
    e_idx = len(f_names)
    if e_idx > len(f_names):
        e_idx = len(f_names)

    t_total = []
    df_t = pd.DataFrame()
    for i in range(s_idx, e_idx):

        f_name = f_names[i]
        f_full = os.path.join(f_dir, f_name) 
        print(f_full)
        f_idx_name, t, df = read_one_file(f_full, 1)

        # print(df.head)
        t_total.extend(t)
        df_t = pd.concat([df_t, df])
        print(df_t.shape)

    if SHOW_FIGURE_TOTAL:
        ShowFigure(df_t, t_total)

    if EXPORT_TO_CSV:
        # f_name = f_names[0]
        for f_name in f_names:
            f_prefix = os.path.splitext(f_name)[0]
            f_csv = f_prefix + ".csv"
            #f_csv = os.path.join(f_prefix, ".csv")
            print("f_csv:", f_csv)
            f_full = os.path.join(f_dir, f_csv) 

            df_t.to_csv(f_full)



    #print(f_idx_name, t, df)

