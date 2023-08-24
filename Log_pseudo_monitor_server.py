import os
import sys

import socket
import signal
import time


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


def main():
    # localIP     = "127.0.0.1"
    localIP     = ""
    localPort   = 61301
    bufferSize  = 80
    cnt = 0

    log = LogFormat101.D_LOG_FORMAT()

    # 데이터그램 소켓을 생성
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    # 주소와 IP로 Bind
    sock.bind((localIP, localPort))
    # sock.setblocking(0)  # set non-blocking socket
    sock.settimeout(1)  # set timeout. 1sec

    print("UDP server up and listening:", localPort)
    # Listen
    while sig_term != 1:
        cnt += 1
        ret = 0
        try:
            # read from UDP
            data, address = sock.recvfrom(bufferSize)
            # p
        except socket.error as err:
            print(err, cnt)
            ret = 0
            if sig_term == 1:
                break
            
        else: 
            #print(address, "recvLen:", len(data))
            ret = len(data)

            log.Unpack(data, 1)     # data, full
            print("t:%d, vtype:%d, vid:%d, (x,y,h):%f,%f,%f" % 
                  (log.t_mainloop, log.vtype, log.vid, log.pos_x, log.pos_y, log.pos_h))

        # time.sleep(0.1)


if __name__ == '__main__':
    main()

