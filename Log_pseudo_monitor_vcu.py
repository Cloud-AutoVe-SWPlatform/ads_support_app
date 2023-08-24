
import os
import sys
import signal

import socket

import time
from datetime import datetime

import math

# sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
# from LogFormat import LogFormat101
import LogFormat101

# signal capture
sig_term = 0
def sig_handler(signum, frame):
    global sig_term
    print("Signal_captured: ", signum)
    sig_term = 1
# Ctrl-C
signal.signal(signal.SIGINT, sig_handler)   # Ctrl+c
signal.signal(signal.SIGTERM, sig_handler)  #

def readable_time(t):
    r_t = t.hour * 10000000 \
               + t.minute * 100000  \
               + t.second * 1000    \
               + int(t.microsecond / 1000)
    return r_t
    

def main():
    # RemoteServerIP      = "127.0.0.1"
    # RemoteServerPort    = 65501
    RemoteServerIP      = "teslasystem.asuscomm.com"
    RemoteServerPort    = 61301
    RemoteServer        = (RemoteServerIP, RemoteServerPort)
    bufferSize  = 80


    #  UDP 소켓 생성
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    log = LogFormat101.D_LOG_FORMAT()
    
    t_last = datetime.now()
    t_sum = 0.0
    while sig_term != 1:
        t_now = datetime.now()
        dt = t_now - t_last
        # t_sum += (dt.seconds)
        t_sum += (dt.microseconds)/1000000.0

        print("", t_now.strftime('%H:%M:%S.%f'), "dt:", dt, "t_sum:", t_sum)

        log.logVersion = 101
        log.vtype = 10
        log.vid = 0
        
        log.t_mainloop = readable_time(t_now)

        log.pos_x = 353549.2611143763
        log.pos_y = 4027619.963927019
        log.pos_h = 180.00 

        log.velocity = 3.0
        log.steering_angle = math.sin(math.radians(t_sum))*540

        if t_sum > 3.0:
            log.system_first_on = 1
            log.evcu_mode = 2
            log.mode_curr = 2
            log.mode_prev = 0

            # GRS80-UTM52N
            log.pos_x = 353549.2611143763
            log.pos_y = 4027619.963927019
            log.pos_h = 180.00 + math.sin(math.radians(t_sum))*180
        # end if


        # 생성된 UDP 소켓을 사용하여 서버로 전송
        sock.sendto(log.Pack(), RemoteServer)

        t_last = t_now
        time.sleep(0.5)     # sleep for 0.1sec


if __name__ == '__main__':
    main()

