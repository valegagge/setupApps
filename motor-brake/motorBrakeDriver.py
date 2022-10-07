# -------------------------------------------------------------------------
# Copyright (C) 2022 iCub Tech - Istituto Italiano di Tecnologia
# This module is the driver for interacting with motor brake.
#
# Valentina Gaggero
# <valentina.gaggero@iit.it>
# -------------------------------------------------------------------------

import sys, time
from numpy import False_
import serial.tools.list_ports as portlist
import serial
import logging
import datetime
import re

import matplotlib.pyplot as plt
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
        self.torque=0.0
        self.speed=0.0
        self.rotation="-"
        self.time = "::"
        self.progNum=0
    def printData(self):
        print(self.time, " torque=", self.torque, " speed= ", self.speed, "rotation=", self.rotation)



#note: how to manage error??? see here https://stackoverflow.com/questions/45411924/python3-two-way-serial-communication-reading-in-data
class MotorBrake:
    "put here the class documentation"

    def __init__(self, comport, baudrate):
        self.cfg=MotorBrakeCfg(comport, baudrate) #is it usefull??
        self.mydata = MotorBrakeOuputData()
        self.serialPort = serial.Serial()
        self.serialPort.baudrate = self.cfg.baudrate
        self.serialPort.port = self.cfg.comport
        self.serialPort.bytesize = 8
        self.serialPort.timeout = 1
        self.serialPort.stopbits = serial.STOPBITS_ONE
        #self.initted=False
    def openSerialPort(self):
        # Set up serial port for read
         
        if not self.serialPort.is_open:
            self.serialPort.open()
            # = serial.Serial(self.cfg.comport, self.cfg.baudrate, bytesize=8, timeout=1, stopbits=serial.STOPBITS_ONE)
            #print('-------------------------------------------------');
            #print('Starting Serial Port', com_port)
    def getDataFake(self):
        self.mydata.torque += 1
        self.mydata.speed +=1
        return self.mydata # check return value or reference
    def getData(self):
        cmd_menu="OD"
        TX_messages = [cmd_menu+dsp6001_end]
        for msg in TX_messages:
            self.serialPort.write( msg.encode() )
        data = self.serialPort.readline().decode()
        if re.search("^S.+T.+R.+",data):
            data_split_str = re.split("[S,T,R,L]", ''.join(data))
            date = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.mydata.speed = float(data_split_str[1])
            self.mydata.torque = float(data_split_str[2])
            self.mydata.rotation = data[12]
            self.mydata.time = date
            self.mydata.progNum +=1

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
