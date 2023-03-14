#/usr/bin
# From sensor datasheet
# https://www.honeywellscportal.com/honeywell-sensing-hpm-series-particle-sensors-datasheet-32322550-e-en.pdf

#from datetime import datetime
#from datetime import date
import time
#import serial
from machine import UART

class part_matt:
    
    def __init__(self, dbg = False):
        self.dbg = dbg
        self.filename = ''
        self.nsample = 0
        
        self.port = UART(1, baudrate = 9600, pins = ('P3','P4'))
        #self.port.init(9600, bits=8, parity=None, stop=1,timeout_chars = 40000)
        if self.dbg == True:
            print('HPM serial connection done')
        self.Read_cmd = [0x68, 0x01, 0x04, 0x93] # Read particle measuring results
        self.Start_cmd = [0x68, 0x01, 0x01, 0x96] # Start particle measurement
        self.Stop_cmd = [0x68, 0x01, 0x02, 0x95] # Stop particle measurement
        self.Set_adj_cmd = [0x68, 0x02, 100, 0x08] # Set adjust cofficient
        self.Get_adj_cmd = [0x68, 0x01, 0x10, 0x87] # Get adjust cofficient
        self.EnaAs_cmd = [0x68, 0x01, 0x40, 0x57] # Enables auto-send
        self.DisAs_cmd = [0x68, 0x01, 0x20, 0x77] # Disables auto-send
        self.pm2p5 = 0.0
        self.pm10 = 0.0
        self.delay = 5
        while self.StopAutoSend() == False:
            time.sleep(self.delay)
        if self.dbg == True:
            print('HPM Autosend stopped')
        time.sleep(0.5)
        while self.StartMeasurement() == False:
            time.sleep(self.delay)
        if self.dbg == True:
            print('HPM Startmeasurement enabled')
        #self.gps = DGPS.Digilent_GPS(self.dbg)
        #self.Acquire_On()
        
    def GetPM2p5_val(self):
        return self.pm2p5

    def GetPM10_val(self):
        return self.pm10
    
    def ReadParticle(self):
        if self.dbg == True:
            self.print_dbg_inf(self.Read_cmd, 'w')
        #self.port.flushInput()
        #self.port.flushOutput()
        self.port.write(bytearray(self.Read_cmd))
        time.sleep(self.delay)
        rcv = self.port.read(8)
        rcv = list(rcv)
        if self.dbg == True:
            self.print_dbg_inf(rcv, 'r')
        if rcv[0] == 0x96 and rcv[1] == 0x96: # NegACK 0x9696
            return False
        if rcv[7] == ((65536 - (sum(rcv) - rcv[7])) % 256):
            if self.dbg == True:
                print('HPM reading done!')
                print('RCV: ',rcv)
            self.pm2p5 = (rcv[3] * 256.0) + rcv[4] # PM2.5 read val in ug/m3
            self.pm10 = (rcv[5] * 256.0) + rcv[6] # PM10 read val in ug/m3
            return True
        else:
            return False
        
    def StartMeasurement(self):
        if self.dbg == True:
            self.print_dbg_inf(self.Start_cmd, 'w')
        #self.port.flushInput()
        #self.port.flushOutput()
        self.port.write(bytearray(self.Start_cmd))
        time.sleep(self.delay)
        rcv = self.port.read(2)
        rcv = list(rcv)
        if self.dbg == True:
            self.print_dbg_inf(rcv, 'r')
        if rcv[0] == 0x96 and rcv[1] == 0x96: # NegACK 0x9696
            return False
        elif rcv[0] == 0xA5 and rcv[1] == 0xA5: # PosACK 0xA5A5
            return True
        else:
            return False

    def StopMeasurement(self):
        if self.dbg == True:
            self.print_dbg_inf(self.Stop_cmd, 'w')
        #self.port.flushInput()
        #self.port.flushOutput()
        self.port.write(bytearray(self.Stop_cmd))
        time.sleep(self.delay)
        rcv = self.port.read(2)
        rcv = list(rcv)
        if self.dbg == True:
            self.print_dbg_inf(rcv, 'r')
        if rcv[0] == 0x96 and rcv[1] == 0x96: # NegACK 0x9696
            return False
        elif rcv[0] == 0xA5 and rcv[1] == 0xA5: # PosACK 0xA5A5
            return True
        else:
            return False

    def SetAdjust(self, newadj):
        if newadj < 30 or newadj > 200:
            return False
        self.Set_adj_cmd[2] = newadjust
        if self.dbg == True:
            self.print_dbg_inf(self.Set_adj_cmd, 'w')
        #self.port.flushInput()
        #self.port.flushOutput()
        self.port.write(bytearray(self.Set_adj_cmd))
        rcv = self.port.read(2)
        rcv = list(rcv)
        if self.dbg == True:
            self.print_dbg_inf(rcv, 'r')
        if rcv[0] == 0x96 and rcv[1] == 0x96: # NegACK 0x9696
            return False
        elif rcv[0] == 0xA5 and rcv[1] == 0xA5: # PosACK 0xA5A5
            return True
        else:
            return False

    def GetAdjust(self):
        if self.dbg == True:
            self.print_dbg_inf(self.Get_adj_cmd, 'w')
        #self.port.flushInput()
        #self.port.flushOutput()
        self.port.write(bytearray(self.Get_adj_cmd))
        time.sleep(self.delay)
        rcv = self.port.read(6)
        rcv = list(rcv)
        if self.dbg == True:
            self.print_dbg_inf(rcv, 'r')
        if rcv[0] == 0x96 and rcv[1] == 0x96: # NegACK 0x9696
            return (-1)
        elif rcv[0] == 0x40 and rcv[1] == 0x02 and rcv[2] == 0x10: # Header (fixed)
            if rcv[4] == ((65536 - sum(rcv) + rcv[5]) % 256):
                return rcv[3]
            return (-1)
        else:
            return (-1)
    
    def StartAutoSend(self):
        if self.dbg == True:
            self.print_dbg_inf(self.EnaAs_cmd, 'w')
        #self.port.flushInput()
        #self.port.flushOutput()
        self.port.write(bytearray(self.EnaAs_cmd))
        time.sleep(self.delay)
        rcv = self.port.read(2)
        rcv = list(rcv)
        if self.dbg == True:
            self.print_dbg_inf(rcv, 'r')
        if rcv[0] == 0x96 and rcv[1] == 0x96: # NegACK 0x9696
            return False
        elif rcv[0] == 0xA5 and rcv[1] == 0xA5: # PosACK 0xA5A5
            return True
        else:
            return False

    def StopAutoSend(self):
        if self.dbg == True:
            self.print_dbg_inf(self.DisAs_cmd, 'w')
        #self.port.flushInput()
        #self.port.flushOutput()
        self.port.write(bytearray(self.DisAs_cmd))
        time.sleep(self.delay)
        rcv = self.port.read(2)
        time.sleep(self.delay)
        rcv = list(rcv)
        if self.dbg == True:
            self.print_dbg_inf(rcv, 'r')
        if rcv[0] == 0x96 and rcv[1] == 0x96: # NegACK 0x9696
            return False
        elif rcv[0] == 0xA5 and rcv[1] == 0xA5: # PosACK 0xA5A5
            return True
        else:
            return False

    def GetAutoSendFrame(self):
        #self.port.flushInput()
        #self.port.flushOutput()
        rcv = self.port.read(32) # Read 32 bytes response
        rcv = list(rcv)
        if self.dbg == True:
            self.print_dbg_inf(rcv, 'r')
        if rcv[0] == 0x42 and rcv[1] == 0x4D: # Fixed frame header
            if rcv[2] == 0x00 and rcv[1] == 28: # Frame length (28 bytes)
                check = (rcv[30] * 256) + rcv[31]
                if check == sum(rcv):
                    self.pm2p5 = (rcv[6] * 256.0) + rcv[7]
                    self.pm10 = (rcv[8] * 256.0) + rcv[9]
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    
    def print_dbg_inf(self, data, txrx):
        if txrx == 'w':
            print('RPI writes to HPM: ', end='')
            for i in data:
                print(hex(i), end=', ')
            print('')
        elif txrx == 'r':
            print('HPM returns to RPI: ', end='')
            for i in data:
                print(hex(i) + ', ', end=', ')
            print('')
            

            
if __name__ == '__main__':
    """
    port = UART(1, baudrate = 9600)
    while port.any() == 0:
        pass
    data = port.read()
    #time.sleep(5)
    print(data)

    """
    
    print('PM sensor test')
    print('Starting sensor ...')
    par_sen = part_matt(dbg = True)
    time.sleep(3)
    sample_time = 1
    i = 0
    #try:
    try:
        while True:
            print('Reading sensor ...')
            while par_sen.ReadParticle() == False:
                pass
            print('PM2.5:', par_sen.GetPM2p5_val(), ', PM10:', par_sen.GetPM10_val(), '[ug/m3]')
            time.sleep(sample_time)
        print('Stopping sensor ...')
        par_sen.StopMeasurement()
        print('End of application')
    except KeyboardInterrupt:
        print('[INFO] Closing')
        par_sen.StopMeasurement() 
        
    
