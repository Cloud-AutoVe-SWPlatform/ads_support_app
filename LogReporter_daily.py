# import tkinter
# from tkinter import filedialog
import os

import struct
import numpy as np
import pandas as pd
#from matplotlib import pyplot as plt
import matplotlib.pyplot as plt

import pickle

import datetime
import LogReader

##################################

# r"string": python raw string
# ROOT_LOG_DIR = r"E:\AVP_LOG_dmz_20220110"
# ROOT_LOG_DIR = "/home/etri01/AVP_LOG_dmz-20220331"
# ROOT_LOG_DIR = r"E:\AVP_LOG_dmz_20220110\VT30-ID06"
ROOT_LOG_DIR = r"E:\AVP_LOG_etri01\sda1\AVP_LOG_tmp"
TARGET_YEAR = "2022"

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

def process_one_day(vinfo, t, df):
    
    # df has one file data
    # check time, mode, reason_mode, distance
    #print(len(t), df.shape)
    results = []

    n = len(t)
    if n == 0:
        # no data
        # results.append([vinfo, clusterT_start, clusterT_end,
        #             loc_s, loc_e,  
        #             clusterNo, clusterIdx_start, clusterIdx_end, reason_mode, clusterDist])
        results.append([vinfo, 0, 0,
                    0, 0,  
                    0, 0, 0, 0, 0])
        return results           

    t_prev = t[0]
    #mode_prev = int(df.iloc[0, 0])  # mode
    mode_prev = int(df['mode'][0])
    if mode_prev == 2:
        mode_prev = 1   # to adjust starting with mode 2

    #reason_mode_prev = int(df.iloc[0, 1])   # reason_mode
    reason_mode_prev = int(df['reason_mode'][0])
    # long_prev = df.iloc[0, 2]   # long
    # lati_prev = df.iloc[0, 3]   # lati
    long_prev = df['long'][0]
    lati_prev = df['lati'][0]
    clusterNo = 0
    clusterStatus = 0
    clusterIdx_start = 0
    clusterIdx_end = 0
    clusterT_start = 0
    clusterT_end = 0

    # cluster_loc_start = (long_prev, lati_prev)
    # cluster_loc_end = (long_prev, lati_prev)

    loc_s = []
    loc_e = []
    clusterDist = 0
    clusterVel = 0.0
    clusterVeln = 0

    results = []
    for i in range(1, n):
        
        t_curr = t[i]
        # mode = int(df.iloc[i, 0])
        # reason_mode = int(df.iloc[i, 1])
        # long = df.iloc[i, 2]
        # lati = df.iloc[i, 3]
        mode = int(df['mode'][i])
        reason_mode = int(df['reason_mode'][i])
        long = df['long'][i]
        lati = df['lati'][i]        

        ##########################
        # set clusterStatus by mode
        if mode == 2 and mode_prev != 2:
            # any mode --> Auto
            clusterStatus = 1

        if mode == 2 and mode_prev == 2:
            # Auto --> Auto
            clusterStatus = 2

        if mode !=2 and mode_prev == 2:
            # Auto --> any mode
            clusterStatus = 3
        
        if mode !=2 and mode_prev != 2:
            clusterStatus = 0

        # end of data
        if i == n-1 and clusterStatus == 2:
            # end of data and on clustering, then finish clustering
            clusterStatus = 3

        ##########################
        # manager clusterStatus
        if clusterStatus == 0:
            # manual
            # set prev
            t_prev = t_curr
            mode_prev = mode
            long_prev = long
            lati_prev = lati

        if clusterStatus == 1:  
            # clustering start
            clusterIdx_start = i
            clusterT_start = t_curr
            clusterDist = 0
            clusterVel = 0.0
            clusterVeln = 0
            loc_s = (long, lati)

            mode_prev = mode

        if clusterStatus == 2:
            # continue clustering
            t_diff = (t_curr - t_prev) / 1000     # sec
            if t_diff >= 1.0:   # over 1 sec
                # Auto mode cluster. cal distance and summation
                dist, vel = get_dist_vel(t_diff, long, lati, long_prev, lati_prev)
                #print("i:%d, t_diff:%0.2f, dist:%.02f, vel:%.02f" % 
                # (i, t_diff, dist, vel))
                if vel > 0.1 and vel < 27.7:
                    clusterDist += dist

                    clusterVel = ((clusterVel*clusterVeln) + vel)/(clusterVeln+1)
                    clusterVeln += 1                    

                # set prev
                t_prev = t_curr
                long_prev = long
                lati_prev = lati
            # mode. always update
            mode_prev = mode 

        if clusterStatus == 3:
            # finalize clustering
            # cal last dist, vel
            # record reasonmode, set total distance. 
            # set clusterStatus to 0
            clusterIdx_end = i
            clusterT_end = t_curr
            loc_e = (long, lati)

            t_diff = (t_curr - t_prev) / 1000     # sec
            dist, vel = get_dist_vel(t_diff, long, lati, long_prev, lati_prev)

            if vel > 0.1 and vel < 27.7:
                clusterDist += dist
                clusterVel = ((clusterVel*clusterVeln) + vel)/(clusterVeln+1)
                clusterVeln += 1                         

            print("(C_NO:%d) Ts:%d, Te:%d, Is:%d, Ie:%d, dist:%.02fm, vel:%.02fm/s" % 
                    (clusterNo, clusterT_start, clusterT_end, clusterIdx_start, 
                    clusterIdx_end, clusterDist, clusterVel))

            results.append([vinfo, clusterT_start, clusterT_end,
                        loc_s, loc_e,  
                        clusterNo, clusterIdx_start, clusterIdx_end, reason_mode, clusterDist])
           
            if clusterT_start > clusterT_end:
                print("Warning:Results: (vinfo, t_start, t_end, clusterNo, idx_s, idx_e, reason_mode, distance)")
            # print(*results, sep='\n')

            clusterNo += 1    
            clusterStatus = 0
            clusterDist = 0
            clusterVel = 0.0
            clusterVeln = 0
            clusterIdx_start = 0
            clusterIdx_end = 0
            # set prev
            t_prev = t_curr
            mode_prev = mode
            long_prev = long
            lati_prev = lati
    
    # if SHOW_PLOT:
    #     # mode
    #     plt.figure()
    #     plt.plot(df.iloc[:, 0])

    #     # location
    #     plt.figure()
    #     plt.plot(df.iloc[:,11], df.iloc[:,12])

    #     plt.show()

    if len(results) == 0:
        results.append([vinfo, 0, 0,
                    0, 0,  
                    0, 0, 0, 0, 0])

    return results

# global variable, 
vkeyDic = {}
entire_log_files = []
def search_new_file(dirname, processed_files):
    try:
        filenames = os.listdir(dirname)

        now = datetime.datetime.now()
        #self.log_day = ""+str(now.year)+"_"+str(now.month)+"_"+str(now.day)
        today = "%04d_%02d_%02d" % (now.year, now.month, now.day)

        match_filenames = [s for s in filenames if today in s]
        if len(match_filenames) == 0:
            print("No Log dir: ", today)
            return None

        # get full name of today's log dir
        today_dir = os.path.join(dirname, match_filenames[0])
        today_logs = os.listdir(today_dir)

        for f_name in today_logs:
            full_filename = os.path.join(today_dir, f_name)
            
            # skip the processed files
            if full_filename in processed_files:
                print("- SKIP: processed file:", full_filename)
                continue
            
            # add new log file
            ext = os.path.splitext(full_filename)[-1]
            if ext == '.idx': 
                #print(full_filename)
                entire_log_files.append(full_filename)

    except Exception as e:
        print(e)
        pass
    
    return entire_log_files

def main(root_log_dir, limit_n_files):

    vinfo_day_idx = []
    vinfo_day_t= []
    vinfo_day_dfs = []

    now = datetime.datetime.now()
    today = "%04d_%02d_%02d" % (now.year, now.month, now.day)
    print(today)

    f_processed_name = "log_processed_daily_"+today+'.pkl'
    f_vinfo_day_name = "vinfo_day_daily_"+today+'.pkl'

    #################################
    # 1. read raw data of today
    processed_files = []    
    if LOAD_RAW_DATA_FROM_PKL:
        try:
            ## Load pickle
            f_path = os.path.join(root_log_dir, f_processed_name)
            with open(f_path,"rb") as fr:
                processed_files = pickle.load(fr)
                print("- Processed File List (%d)" % len(processed_files))
                print(*processed_files, sep='\n')

            f_path = os.path.join(root_log_dir, f_vinfo_day_name)
            with open(f_path, "rb") as fr:
                vinfo_day_idx, vinfo_day_t, vinfo_day_dfs = pickle.load(fr) 
                # vinfo_day_idx = data[0]
                # vinfo_day_t = data[1]
                # vinfo_day_dfs = data[2]
                print("Load Pickel:", len(vinfo_day_idx), len(vinfo_day_t), len(vinfo_day_dfs))           
            print("Load OK:", f_processed_name, f_vinfo_day_name)

        except:
            f_path = os.path.join(root_log_dir, f_processed_name)            
            print("ERROR:No file: %s. Skip Loading" % str(f_path))

    ###############################
    # search_new_file returns entire_file_list
    new_files = search_new_file(root_log_dir, processed_files)
    #print(*new_files, sep='\n')


    ########################
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
    if limit_n_files == -1:
        limit_n_files = nfiles
    for i_f in range(nfiles):

        if i_f >= limit_n_files:
            break; 
    
        f_full = new_files[i_f]
        print("- Processing Files(%d/%d) - %s" % (i_f, nfiles, f_full))
        processed_f_name, t, df = LogReader.read_one_file(f_full)
        #print(df)

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
            
            # pandas.concat 에서 ignore_index 가 없으면 다시 0부터 시작함
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
                f_path = os.path.join(root_log_dir, f_processed_name)            
                with open(f_path,"wb") as fw:
                    pickle.dump(processed_files, fw)

                f_path = os.path.join(root_log_dir, f_vinfo_day_name)            
                with open(f_path,"wb") as fw:
                    data = [vinfo_day_idx, vinfo_day_t, vinfo_day_dfs]
                    print("Dump:vinfo_day:", len(vinfo_day_idx), len(vinfo_day_t), len(vinfo_day_dfs))
                    pickle.dump(data, fw)

    if SAVE_RAW_DATA_TO_PKL and nfiles > 0:
        print("SAVE pkl- final (%d/%d)" % (i_f, nfiles))
        f_path = os.path.join(root_log_dir, f_processed_name)            
        with open(f_path,"wb") as fw:
            pickle.dump(processed_files, fw)

        f_path = os.path.join(root_log_dir, f_vinfo_day_name)            
        with open(f_path,"wb") as fw:
            data = [vinfo_day_idx, vinfo_day_t, vinfo_day_dfs]
            print("Dump:vinfo_day:", len(vinfo_day_idx), len(vinfo_day_t), len(vinfo_day_dfs))
            pickle.dump(data, fw)


    #################################
    # 2. Calculate all_automode
    # No append allowed. Just Load or Calculate all
    sum_vinfo_all_automode = []
    f_name_all_automode = 'sum_vinfo_all_automode_'+today+'.pkl'
    if LOAD_ALL_AUTOMODE_FROM_PKL:
        print("SKIP: Calculate all automode. Load from pkl ")
        f_path = os.path.join(root_log_dir, f_name_all_automode)        
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
            f_path = os.path.join(root_log_dir, f_name_all_automode)            
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

    # ##############################
    # # 월별 주행거리 합산
    # vinfo_month_prev = []
    # dist_month = [] 
    # sum_vinfo_month = []
    # for i in range(len(sum_vinfo_day)):
    #     sum_vinfo = sum_vinfo_day[i]
    #     vinfo_month = sum_vinfo[0][0:-1]
    #     dist = sum_vinfo[1]
    #     try:
    #         idx = vinfo_month_prev.index(vinfo_month)
    #         dist_month[idx] += dist
    #     except:
    #         #no index
    #         #print("Add new vinfo_month", vinfo_month)
    #         vinfo_month_prev.append(vinfo_month)
    #         dist_month.append(dist)

    # for i in range(len(vinfo_month_prev)):
    #     # append the final month
    #     sum_vinfo_month.append([vinfo_month_prev[i], dist_month[i]])

    # sum_vinfo_month.sort()

    # print("- Result per Month(km)")
    # print(*sum_vinfo_month, sep='\n')

    # ##############################
    # # 반기별, 전체 주행거리 합산
    # # ('vt10', 'id01', '2021', '09') --> ('vt10', 'id01', '2021')
    # #vinfo_year_prev = sum_vinfo_month[0][0][0:-1]
    # vinfo_year_prev = []
    # dist_1st_half = []
    # dist_2nd_half = []
    # dist_year = []
    # sum_vinfo_year = []
    # for i in range(len(sum_vinfo_month)):
    #     sum_vinfo = sum_vinfo_month[i]
    #     vinfo_year = sum_vinfo[0][0:3]     # ('vt10', 'id01', '2021')
    #     vinfo_month = sum_vinfo[0][3]
    #     month = int(vinfo_month)
    #     dist = sum_vinfo[1]
    #     try:
    #         idx = vinfo_year_prev.index(vinfo_year)
    #         dist_year[idx] += dist
    #         if month <= 6:
    #             dist_1st_half[idx] += dist
    #         else:
    #             dist_2nd_half[idx] += dist
    #     except:
    #         vinfo_year_prev.append(vinfo_year)
    #         dist_year.append(dist)
    #         if month <= 6:
    #             dist_1st_half.append(dist)
    #             dist_2nd_half.append(0)
    #         else:
    #             dist_1st_half.append(0)
    #             dist_2nd_half.append(dist)

    # for i in range(len(vinfo_year_prev)):
    #     # append the final month
    #     sum_vinfo_year.append([vinfo_year_prev[i], dist_1st_half[i], dist_2nd_half[i], dist_year[i]])
            
    # sum_vinfo_year.sort()

    # print("- Result per Year(km): 1st half, 2nd half, full year")
    # print(*sum_vinfo_year, sep='\n')

    ##########################
    # 4. 결과 txt로 저장
    now = datetime.datetime.now()
    nowDate = now.strftime('%Y_%m_%d')      # 2021-04-19
    nowTime = now.strftime('%H:%M:%S')      # 12h-11m-21s
    print(nowTime)      # 12:11:32

    f_result = os.path.join(root_log_dir, 'result_'+nowDate+'-daily.txt')      
    with open(f_result, "w") as f:
        #f.write(*sum_vinfo_year, sep='\n')

        # f.write("- Result per Year(km): 1st half, 2nd half, full year\n")        
        # result = '\n'.join(str(s) for s in sum_vinfo_year)
        # f.write(result)
        # f.write("\n")

        # f.write("- Result per Month(km)\n")
        # result = '\n'.join(str(s) for s in sum_vinfo_month)
        # f.write(result)
        # f.write("\n")

        f.write("- Result per Day(km)\n")
        result = '\n'.join(str(s) for s in sum_vinfo_day)
        f.write(result)
        f.write("\n")    



# 로그데이터 로딩 자체에 시간이 많이 걸리고, 계산에는 얼마 걸리지 않음. 
# 그래서 한번 로딩한 것은 피클로 저장해서 다시 로드해서 사용
# 계산은 각 날짜에 다시 추가되는 것이 있으므로, 
# 처음부터 다시 계산하던지, 아니면 아예 로드해서(추가없이) 사용할 것
LOAD_RAW_DATA_FROM_PKL = 1
LOAD_ALL_AUTOMODE_FROM_PKL = 0      # No append allowed. Just Load or Calculate all
SAVE_RAW_DATA_TO_PKL = 1
SAVE_ALL_AUTOMODE_TO_PKL = 1

SKIP_VIRTUAL_VEHICLE = 1

SHOW_PLOT = 0

if __name__ == '__main__':
    # daily reporting sw
    # need to set vt-id at the root_log_dir
    #root_log_dir = "/home/etri01/AVP_LOG_tmp"
    # r"string": python raw string
    #ROOT_LOG_DIR = r"E:\AVP_LOG_dmz_20220110\VT30-ID06"

    limit_n_files = -1   # max number of new files. -1:max, 0:no new file
    main(ROOT_LOG_DIR, limit_n_files)

