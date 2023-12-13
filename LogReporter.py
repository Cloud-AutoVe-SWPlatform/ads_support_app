# import tkinter
# from tkinter import filedialog
import os

import struct
import numpy as np
import pandas as pd
#from matplotlib import pyplot as plt
import matplotlib.pyplot as plt
import math

import pickle

import datetime
import LogReader

##################################

# r"string": python raw string
# ROOT_LOG_DIR = r"E:\AVP_LOG_dmz_20220110"
# ROOT_LOG_DIR = "/home/etri01/AVP_LOG_dmz-20220331"
#ROOT_LOG_DIR = r"E:\AVP_LOG_etri01\sda1\AVP_LOG_tmp"
# ROOT_LOG_DIR = r"E:\22_AVP_LOG\AVP_LOG_distance_2"
# ROOT_LOG_DIR = r"E:\22_AVP_LOG\AVP_LOG_dmz\AVP_LOG_tmp"
#ROOT_LOG_DIR = r"E:\22_AVP_LOG\AVP_LOG_tmp\2023_10\VT40-ID01"   # 2023.12.06
ROOT_LOG_DIR = r"E:\22_AVP_LOG\AVP_LOG_oci" # 2023.12.07
LIMIT_N_FILES = -1   # max number of new files. -1:max, 0:no new file
TARGET_YEAR = 2023

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
    mode_prev = int(df['5.evcuMode'][0])
    if mode_prev == 2:
        mode_prev = 1   # to adjust starting with mode 2

    #reason_mode_prev = int(df.iloc[0, 1])   # reason_mode
    reason_mode_prev = int(df['6.reasonMode'][0])
    # long_prev = df.iloc[0, 2]   # long
    # lati_prev = df.iloc[0, 3]   # lati
    long_prev = df['15.pos_x'][0]
    lati_prev = df['16.pos_y'][0]
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
        mode = int(df['5.evcuMode'][i])
        reason_mode = int(df['6.reasonMode'][i])
        long = df['15.pos_x'][i]
        lati = df['16.pos_y'][i]
        long_last = df['15.pos_x'][i-1]
        lati_last = df['16.pos_y'][i-1]

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
            # cal last dist, vel - use prev
            # record reasonmode, set total distance. 
            # set clusterStatus to 0
            clusterIdx_end = i
            clusterT_end = t_curr

            # update: 2023.11.03
            # Use last loc, not curr loc.
            # loc_e = (long, lati)
            loc_e = (long_last, lati_last)

            t_diff = (t_curr - t_prev) / 1000     # sec
            dist, vel = get_dist_vel(t_diff, long_last, lati_last, long_prev, lati_prev)

            if vel > 0.1 and vel < 27.7:
                clusterDist += dist
                clusterVel = ((clusterVel*clusterVeln) + vel)/(clusterVeln+1)
                clusterVeln += 1                         

            print("(C_NO:%d) Ts:%d, Te:%d, Is:%d(%.02f,%.02f), Ie:%d(%.02f,%.02f), dist:%.02fm, vel:%.02fm/s" % 
                    (clusterNo, clusterT_start, clusterT_end, clusterIdx_start, long_prev, lati_prev,
                    clusterIdx_end, long_last, lati_last, clusterDist, clusterVel))

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
            long_prev = long_last
            lati_prev = lati_last
    
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
                try:
                    last_dir = full_filename.split(DIR_SEP)[-1]
                    curr_dir = last_dir.split('-')


                    search_new_file(full_filename, processed_files)

                    ########################3
                    # check TARGET_YEAR
                    # if curr_dir[0] == 'LOGv4':
                    #     if int(curr_dir[-1][0:4]) == TARGET_YEAR:
                    #         # if curr_dir is LOGv4~~~ with target year, add that dir
                    #         # or do nothing
                    #         search_new_file(full_filename, processed_files)
                    #     else:
                    #         print("TARGET_YEAR missmatch. skip:", curr_dir[-1])
                    # else:
                    #     search_new_file(full_filename, processed_files)


                except:
                    None
            else:
                ext = os.path.splitext(full_filename)[-1]
                if ext == '.idx': 
                    #print(full_filename)
                    entire_log_files.append(full_filename)
    except PermissionError:
        pass
    
    #print(vkeyDic)
    return entire_log_files

entire_log_folders = []
def search_new_folder(dirname, processed_folders):

    try:
        f_lists = os.listdir(dirname)
        for filename in f_lists:
            #print(filename.split('-'))
            full_name = os.path.join(dirname, filename)
            
            if SKIP_VIRTUAL_VEHICLE:
                try:
                    vid = filename.split('-')[1]
                    if vid == "ID00":
                        # virtual vehicle
                        print("- SKIP: VIRTUAL_VEHICLE:", full_name)
                        continue                    
                except:
                    None

            # skip the processed files
            if full_name in processed_folders:
                print("- SKIP: processed file:", full_name)
                continue

            if os.path.isdir(full_name):
                try:
                    # day dir form : vt40-id01-2023_09_06
                    vtype, vid, year_month_day = filename.split('-')
                    l_year, l_month, l_day = year_month_day.split('_')

                    if vtype[0:2] == 'vt' and vid[0:2] == 'id':
                        # add to final log_folder list
                        entire_log_folders.append(full_name)

                except:
                    # Not final year_month_day dir
                    # go to deeper
                    # print("Error: split year_month_day:", full_filename)
                    search_new_folder(full_name, processed_folders)

            else:
                # file : do Nothing
                # ext = os.path.splitext(full_name)[-1]
                # if ext == '.idx': 
                #     #print(full_filename)
                #     entire_log_files.append(full_name)
                None

    except PermissionError:
        pass
    
    #print(vkeyDic)
    return entire_log_folders


def get_info_curr(f_full):

    terms = f_full.split(DIR_SEP)
    ###################################
    # log file processing
    # terms = f_full.split(DIR_SEP)        
    # version 5
    if terms[-1][0:2] == 'vt':
        # log version 5: LOGv4-vt30-id00-2021_10_14/vt00-id00-12h_34m_56s-X000000-Y000000.idx
        # days
        days = terms[-2].split('-')[-1]     # 2021_10_06
        year, month, day = days.split('_')  # string, 2021, 10, 06

        id_time = terms[-1].split('-')     # vt00-id00-10h_35m_19s-X000000-Y000000.idx
        vtype, vid = id_time[0], id_time[1]
        hh, mm, sec = id_time[2].split('_')      # string

        info_curr = (vtype, vid, year, month, day)
        # info_prev = (vtype_prev, vid_prev, year_prev, month_prev, day_prev)
    else:
        # log version 6: vt50-id51-2023_09_05/11h_01m_11s-X37.238760-Y126.772715.idx
        # days
        vtype, vid, days = terms[-2].split('-')     # vt50, id51, 2021_10_06
        year, month, day = days.split('_')          # string, 2021, 10, 06

        t_hhmmss, xloc, yloc = terms[-1][0:-4].split('-')              # 11h_01m_11s, X37.238760, Y126.772715.idx
        # print(t_hhmmss, xloc, yloc)
        hh, mm, sec = t_hhmmss.split('_')      # string

        info_curr = (vtype, vid, year, month, day)
        # info_prev = (vtype_prev, vid_prev, year_prev, month_prev, day_prev)
    
    return info_curr


def Worker(root_log_dir, limit_n_files):

    # total_files = []
    processed_files = []
    processed_folders = []
    # processed_t = []
    # processed_dfs = []

    vinfo_day_idx = []
    vinfo_day_t= []
    vinfo_day_dfs = []

    #################################
    # 1. read raw data from pkl
    if LOAD_RAW_DATA_FROM_PKL:
        try:
            ## Load pickle
            f_path = os.path.join(root_log_dir, "log_processed.pkl")
            with open(f_path,"rb") as fr:
                processed_files = pickle.load(fr)
                print("- Processed File List (%d)" % len(processed_files))
                print(*processed_files, sep='\n')

            f_path = os.path.join(root_log_dir, "vinfo_day.pkl")
            with open(f_path, "rb") as fr:
                vinfo_day_idx, vinfo_day_t, vinfo_day_dfs = pickle.load(fr) 
                # vinfo_day_idx = data[0]
                # vinfo_day_t = data[1]
                # vinfo_day_dfs = data[2]
                print("Load Pickel:", len(vinfo_day_idx), len(vinfo_day_t), len(vinfo_day_dfs))           
            print("log_processed.pkl loaded")

        except:
            f_path = os.path.join(root_log_dir, "log_processed.pkl")            
            print("SKIP_PKL_LOADING:No file: %s. Skip Loading" % str(f_path))

    ###############################
    # search_new_file entire_file_list
    new_files = search_new_file(root_log_dir, processed_files)
    # important. file sorting
    new_files.sort()

    new_folders = search_new_folder(root_log_dir, processed_folders)
    new_folders.sort()

    nfiles = len(new_files)
    nfolders = len(new_folders)
    print("Total:%d log files" % (nfiles))
    print("Total:%d log folders" % (nfolders))

    ###############################
    # Processing folders

    # if limit_n_folders == -1:
    #     limit_n_folders = nfolders
    # for i_f in range(nfolders):

    #     if i_f >= limit_n_files:
    #         break; 
    
    #     f_full = new_files[i_f]
    #     terms = f_full.split(DIR_SEP)

    #     print("- Processing(%d/%d) - %s/%s" % (i_f, nfiles, terms[-2], terms[-1]))



    ###############################
    # Processing files
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
        terms = f_full.split(DIR_SEP)

        print("- Processing(%d/%d) - %s/%s" % (i_f, nfiles, terms[-2], terms[-1]))

        # #terms = f_full.split('\\')
        # terms = f_full.split(DIR_SEP)
        # #print("terms:", terms)

        # # check TARGET_YEAR
        # c_year = terms[-2].split('-')[-1]
        # if int(c_year) != TARGET_YEAR:
        #     print("SKIP: not TARGET_YEAR. Skip a file:", *terms)
        #     print("TARGET_YEAR", TARGET_YEAR, "- terms[-4]:", terms[-4][0:4])
        #     continue

        # # terms[-2]: LOGv4-vt00-id00-2021_10_06
        # if terms[-2][0:5] != "LOGv4":
        #     print("Error: violate log_dir structure. Skip a file:", terms)
        #     print("terms[-2]:", terms[-2][0:5])
        #     continue

        # info_curr = (vtype, vid, year, month, day)
        processed_f_name, t_logs, df, info_curr = LogReader.read_one_file(f_full, GET_FULL_LOG, 0, 0)
        #print(df)

        # filename, dataframe pair
        processed_files.append(processed_f_name)

        # ###################################
        # # log file processing
        # # terms = f_full.split(DIR_SEP)        
        # # version 5
        # if terms[-1][0:2] == 'vt':
        #     # log version 5: LOGv4-vt30-id00-2021_10_14/vt00-id00-12h_34m_56s-X000000-Y000000.idx
        #     # days
        #     days = terms[-2].split('-')[-1]     # 2021_10_06
        #     year, month, day = days.split('_')  # string, 2021, 10, 06

        #     id_time = terms[-1].split('-')     # vt00-id00-10h_35m_19s-X000000-Y000000.idx
        #     vtype, vid = id_time[0], id_time[1]
        #     hh, mm, sec = id_time[2].split('_')      # string

        #     info_curr = (vtype, vid, year, month, day)
        #     info_prev = (vtype_prev, vid_prev, year_prev, month_prev, day_prev)
        # else:
        #     # log version 6: vt50-id51-2023_09_05/11h_01m_11s-X37.238760-Y126.772715.idx
        #     # days
        #     vtype, vid, days = terms[-2].split('-')     # vt50, id51, 2021_10_06
        #     year, month, day = days.split('_')          # string, 2021, 10, 06

        #     t_hhmmss, xloc, yloc = terms[-1][0:-4].split('-')              # 11h_01m_11s, X37.238760, Y126.772715.idx
        #     # print(t_hhmmss, xloc, yloc)
        #     hh, mm, sec = t_hhmmss.split('_')      # string

        #     info_curr = (vtype, vid, year, month, day)
        #     info_prev = (vtype_prev, vid_prev, year_prev, month_prev, day_prev)

        # info_curr = (vtype, vid, year, month, day)
        # info_curr = get_info_curr(f_full)

        # append data for each day
        if info_curr in vinfo_day_idx:
            idx = vinfo_day_idx.index(info_curr)
            df_prev = vinfo_day_dfs[idx]
            t_prev = vinfo_day_t[idx]
            #print(len(t_prev), df_prev.shape)
            
            # ignore_index 가 없으면 다시 0부터 시작함
            vinfo_day_dfs[idx] = pd.concat([df_prev, df], ignore_index=True)
            vinfo_day_t[idx].extend(t_logs)
            #print(len(vinfo_day_t), vinfo_day_dfs[idx].shape)

            #plt.figure(str(vinfo_day_idx[idx]))
            #plt.plot(vinfo_day_t[idx])
            #plt.show()

        else:
            vinfo_day_idx.append(info_curr)
            vinfo_day_t.append(t_logs)
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
        
        dist_day  = math.trunc(dist_day/100)/10
        sum_vinfo_day.append([vinfo_day, dist_day])

    sum_vinfo_day.sort()

    print("- Results per Day(km)")
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

    print("- Results per Month(km)")
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

    print("- Results per Year(km): 1st half, 2nd half, full year")
    print(*sum_vinfo_year, sep='\n')

    total_dist = 0
    for i_sum in sum_vinfo_year:
        total_dist += i_sum[3]
    print("- Results Total: ", total_dist, 'km')

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

            f.write("- Result Total: %.02fkm\n" % (total_dist))
 
            f.write("- Results per Year(km): 1st half, 2nd half, full year\n")        
            result = '\n'.join(str(s) for s in sum_vinfo_year)
            f.write(result)
            f.write("\n")

            f.write("- Results per Month(km)\n")
            result = '\n'.join(str(s) for s in sum_vinfo_month)
            f.write(result)
            f.write("\n")

            f.write("- Results per Day(km)\n")
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

if __name__ == '__main__':
    #new_files = search_new_file("E:\AVP_LOG_dmz", processed_files)
    #new_files = search_new_file("C:\AVP_LOG\AVP_LOG_dmz_tmp", processed_files)
    #new_files = search_new_file("E:\AVP_LOG_dmz_tmp", processed_files)

    #root_log_dir = "E:\AVP_LOG_dmz"
    #root_log_dir = "E:\AVP_LOG_dmz_tmp"
    #root_log_dir = "C:\AVP_LOG\AVP_LOG_dmz_tmp2"
    #root_log_dir = "/media/etri01/T7/AVP_LOG_dmz"
    #root_log_dir = "/home/etri01/AVP_LOG_tmp"
    #root_log_dir = "/home/etri01/AVP_LOG_dmz-20220331"
    # r"string": python raw string
    #root_log_dir = r"E:\AVP_LOG_dmz_20220110"

    # LIMIT_N_FILES = 1   # max number of new files. -1:max, 0:no new file
    # main(ROOT_LOG_DIR, limit_n_files)
    Worker(ROOT_LOG_DIR, LIMIT_N_FILES)

