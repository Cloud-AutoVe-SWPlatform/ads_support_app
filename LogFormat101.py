import struct

class D_LOG_FORMAT:
    def __init__(self):
        self.nFields = 22    # nFields         
        self.fmf = '<'      # little endian
        
        self.logVersion = 0         # 0, u8
        self.vtype = 0              # 1, u8
        self.vid = 0                # 2, u8
        self.system_first_on = 0    # 3, u8, B
        self.t_mainloop = 0         # 4, u32, I
        self.fmf += '4BI'           # total size: 8

        self.evcu_mode = 0          # 5
        self.reason_mode = 0        # 6
        self.mode_prev = 0          # 7
        self.mode_curr = 0          # 8
        self.event1 = 0             # 4,
        self.event2 = 0             # 
        self.error1 = 0             #
        self.error2 = 0             # 
        self.warning1 = 0           # 
        self.warning2 = 0           # 14
        self.fmf += '10B'           # total size: 18

        self.pos_x = 0.0            # 15, f64(double), d
        self.pos_y = 0.0            # 16, f64(double), d
        self.pos_h = 0.0            # 17, f32(float), f
        self.velocity = 0.0         # 18, f32(float), f
        self.steering_angle = 0.0   # 19, f32(float), f
        self.fmf += 'ddfff'         # total size: 46

        self.gps_time = 0.0         # 20, f64(double), d
        self.gps_pos_x = 0.0        # 21
        self.gps_pos_y = 0.0        # 22
        self.fmf += 'ddd'           # total size: 70

        self.reserved = [0]*10         # 10 byte
        self.fmf += '10B'


    def Pack(self):
        # pack of list
        # https://stackoverflow.com/questions/16368263/python-struct-pack-for-individual-elements-in-a-list
        # buf = struct.pack('d'*NumElements,data)  # Returns error
        # buf = struct.pack('d'*NumElements, *data) # Works

        data = struct.pack(self.fmf, 
            self.logVersion, self.vtype, self.vid, self.system_first_on, self.t_mainloop, 
            self.evcu_mode, self.reason_mode, self.mode_prev, self.mode_curr, 
            self.event1, self.event2, self.error1, self.error2, self.warning1, self.warning2, 
            self.pos_x, self.pos_y, self.pos_h, self.velocity, self.steering_angle, 
            self.gps_time, self.gps_pos_x, self.gps_pos_y, 
            *self.reserved)
        
        return data

    def Unpack(self, rdata, full):
        
        #print('rdata:', len(rdata))

        data = struct.unpack(self.fmf, rdata)
        # print(data)
        # self.VIEW_msg = data[0]

        self.logVersion, self.vtype, self.vid, self.system_first_on, self.t_mainloop, \
            self.evcu_mode, self.reason_mode, self.mode_prev, self.mode_curr, \
            self.event1, self.event2, self.error1, self.error2, self.warning1, self.warning2, \
            self.pos_x, self.pos_y, self.pos_h, self.velocity, self.steering_angle, \
            self.gps_time, self.gps_pos_x, self.gps_pos_y, \
            *self.reserved \
            = struct.unpack(self.fmf, rdata)

        if full == 0:
            # only return small data
            # time, mode, reason_mode, long, lati, heading
            pdata = [data[4], data[5], data[6], data[15], data[16], data[17]]
        else:
            # return full data
            pdata = data
            #print("len(pdata):", len(pdata))

        # save nFields after first parsing
        if self.nFields == 0:
            self.nFields = len(pdata)
            print("nFields:", self.nFields)

        #self.pd_log = pd.Series(data)
        #print(self.pd_log)
        return pdata

    def getnField(self):
        # len(pdata)
        return self.nFields

    def getColumnNames(self, isfull):
        if isfull:
            self.c_names = list(map(str, range(self.nFields)))
            print('nFields:', self.nFields)

            self.c_names[0:5] = ['0.LogV', '1.vType', '2.vId', '3.res', '4.t_mainLoop']
            self.c_names[5:15] = ['5.evcuMode', '6.reasonMode', '7.modePrev', '8.modeCurr', \
                '9.event1', '10.event2', '11.error1', '12.error2', '13.warning1', '14.warning2']
            self.c_names[15:20] = ['15.pos_x', '16.pos_y', '17.pos_h', '18.velocity','19.steeringAngle']
            self.c_names[20:23] = ['20.gps_time', '21.gps_pos_x', '22.gps_pos_y']
        else:
            self.c_names = ['time', 'mode', 'reason_mode', 'long', 'lati', 'heading']
        return self.c_names


    def getsize(self):
        return struct.calcsize(self.fmf)

if __name__ == '__main__':

    log = D_LOG_FORMAT()
    print('fmf:', log.fmf, log.getsize())

