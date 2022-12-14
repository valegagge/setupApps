# -------------------------------------------------------------------------
# Copyright (C) iCub Tech - Istituto Italiano di Tecnologia (IIT)
#
# This module is the driver for interacting with motor brake Magtrol DSP6001 device.
#
# Valentina Gaggero
# <valentina.gaggero@iit.it>
# -------------------------------------------------------------------------


import serial
import datetime
import re
import time
import numpy as np

from datetime import datetime
from termcolor import colored
from colorama import init

# -------------------------------------------------------------------------
# General
# -------------------------------------------------------------------------
com_menu = 1
cmd_menu = 1
com_port = ''
# Answer format 'S    0T0.488R\r\n'

# -------------------------------------------------------------------------
# DSP6001 COMMAND SET
# -------------------------------------------------------------------------
dsp6001_cmd = [
    "*IDN?",         # Returns Magtrol Identification and software revision
    "OD",            # Prompts to return speed-torque-direction data string
    "PR",            # 
    "Q#",            # 
    "N#",            # 
    "Custom",        # 
    "Quit"           # Exit
    ]
dsp6001_end = "\r\n"



class MotorBrakeCfg:
    def __init__(self, comport, baudrate=9600):
        self.comport=comport
        self.baudrate=baudrate

class MotorBrakeOuputData:
    def __init__(self) -> None:
        self.torque=0.0 #Nm
        self.speed=0.0  #deg/sec
        self.rotation="-"
        self.time = "::"
        self.progNum=0
    def printData(self):
        print(self.time, " torque[Nm]=", self.torque, " speed[deg/sec]= ", self.speed, "rotation=", self.rotation)



#note: how to manage error??? see here https://stackoverflow.com/questions/45411924/python3-two-way-serial-communication-reading-in-data
class MotorBrake:
    "This is the documentation for class MotorBrake"

    def __init__(self, comport, baudrate):
        self.cfg=MotorBrakeCfg(comport, baudrate) #is it usefull??
        self.mydata = MotorBrakeOuputData()
        self.serialPort = serial.Serial()
        self.serialPort.baudrate = self.cfg.baudrate
        self.serialPort.port = self.cfg.comport
        self.serialPort.bytesize = 8
        self.serialPort.timeout = 1
        self.serialPort.stopbits = serial.STOPBITS_ONE
        self.time_array = np.array([])
        self.acqTimingIsEna = False
        self.acqTimingPeriod = 1
        self.acqTimingStart = 0

    def openSerialPort(self):
        # Set up serial port for read
        try: 
            if not self.serialPort.is_open:
                self.serialPort.open()
            return True
        except serial.serialutil.SerialException:
            return False


    def getDataFake(self):
        self.mydata.torque += 1
        self.mydata.speed +=1
        return self.mydata # check return value or reference
    def getData(self):
        cmd_menu="OD"
        TX_messages = [cmd_menu+dsp6001_end]
        start_time = time.time()
        for msg in TX_messages:
            self.serialPort.write( msg.encode() )
        data = self.serialPort.readline().decode()
        self.mydata.time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.mydata.progNum +=1
        if re.search("^S.+T.+R.+",data):
            data_split_str = re.split("[S,T,R,L]", ''.join(data))
            self.mydata.speed = (float(data_split_str[1])*60/360) #60/360 to transform from deg/sec to rpm
            self.mydata.torque = (float(data_split_str[2])/1000) #/1000 to transform from mNm to Nm
            self.mydata.rotation = data[12]
            
        curr_time = time.time() 
        
        if self.acqTimingIsEna == True:
            self.time_array = np.append (self.time_array, curr_time-start_time)
            
            if(curr_time - self.acqTimingStart > self.acqTimingPeriod):
                print("\n")
                print(colored('----- STATISTIC -------', 'blue'))
                mystr = "mean = " + str(np.mean(self.time_array))
                print(colored(mystr, 'blue') )
                mystr = "std = " + str(np.std(self.time_array))
                print(colored(mystr, 'blue') )
                mystr = "var = " + str(np.var(self.time_array))
                print(colored(mystr, 'blue') )
                mystr = "min = " + str(np.min(self.time_array))
                print(colored(mystr, 'blue') )
                mystr = "max = " + str(np.max(self.time_array))
                print(colored(mystr, 'blue') )
                print(colored('-----------------------', 'blue'))
                
                self.time_array.resize(0)
                self.acqTimingStart = curr_time

        return self.mydata # check return value or reference
    
    def closeSerialPort(self):
        if self.serialPort.is_open:
            self.serialPort.close()
    def sendCommand(self, command):
        self.__sendData(command)

    def sendTorqueSetpoint(self, trq):
        setpoint = "Q"+str(trq)
        self.__sendData(setpoint)


    def sendSpeedSetpoint(self, trq):
        setpoint = "N"+str(trq)
        self.__sendData(setpoint)
    
    def disableAcquisitionTiming(self):
        self.acqTimingIsEna = False

    def enableAcquisitionTiming(self, period):
        self.acqTimingIsEna = True
        self.acqTimingPeriod = period
        self.time_array.resize(0)
        self.acqTimingStart = time.time()

    def __sendData(self, cmd): #private method
        if self.serialPort.is_open:
            try:
                TX_messages = [cmd+dsp6001_end]
                for msg in TX_messages:
                    self.serialPort.write(msg.encode())
                    print(colored('\nMagtrol says:', 'yellow'), self.serialPort.readline().decode())
                    return True
            except Exception as e:
                print ("Error communicating...: " + str(e))
                return False
        else:
            print ("Cannot open serial port.")
            return False

