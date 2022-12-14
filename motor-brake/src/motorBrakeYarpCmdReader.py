# -------------------------------------------------------------------------
# Copyright (C) iCub Tech - Istituto Italiano di Tecnologia (IIT)
#
# Here is defined the MotorBrakeYarpCmdReader class and its help classes,
# that takes care to receive a command from the input yarp port and forwards
# it to the motor-brake device.
#
# Written by V. Gaggero
# <valentina.gaggero@iit.it>
# -------------------------------------------------------------------------

from concurrent.futures import thread
import serial.tools.list_ports as portlist
import yarp
from threading import Thread
from threading import Event
from threading import Lock
from src.motorBrakeDriver import MotorBrake as MotBrDriver
import matplotlib.pyplot as plt
from termcolor import colored
from colorama import init
import sys
import argparse
import time

#-------------------------------------------------------------------------------
# Here two classes are defined:
#  - MotorBrakeYarpCmdReader: it is a thread started by the main process
#    that creates the DataProcessor object and manages the stop event
#  - DataProcessor: it has the goal of listening to the port /motorbrake/cmd:i
#    and processes any received command: if the command has been parsed successfully 
#    it forwards the command to the motor-brake's driver else the command is ignored.
#-------------------------------------------------------------------------------

class DataProcessor(yarp.PortReader):
    def __init__(self, motor_br_dev, lock):
        super().__init__()
        self.lock = lock
        self.motor_br_dev = motor_br_dev
    
    def read(self,connection):
        if not(connection.isValid()):
            print("MotorBrakeYarpCmdReader: connection not valid...closing")
            return False
        bin = yarp.Bottle()
        print("Trying to read from connection")
        ok = bin.read(connection)
        if not(ok):
            print("MotorBrakeYarpCmdReader: failed to read input")
            return False
        self.__parseCommand(bin.toString())
        print("Received [%s]"%bin.toString())
        return True
        #removed rensponce
        # bout.addString("Received:")
        # bout.append(bin)
        # print("Sending [%s]"%bout.toString())
        # writer = connection.getWriter()
        # if writer==None:
        #     print("No one to reply to")
        #     return True
        # return bout.write(writer)
    

    def __parseCommand(self, strCmd):
        cmdList = strCmd.split()
        if len(cmdList)==0:
            return False
        if cmdList[0] == 'torque':
            val = float(cmdList[1])
            with self.lock:
                self.motor_br_dev.sendTorqueSetpoint(val)
            print("MotorBrakeYarpCmdReader sends torque=", val)
        elif  cmdList[0] == 'speed':
            val = float(cmdList[1])
            with self.lock:
                self.motor_br_dev.sendSpeedSetpoint(val)
            print("MotorBrakeYarpCmdReader sends speed=", val)
        else:
            print("MotorBrakeYarpCmdReader command unknown!! ", cmdList[0])
            return False
        
        return True






class MotorBrakeYarpCmdReader (Thread):
    def __init__(self, motor_br_dev, stopEvt, lock):
        Thread.__init__(self)
        self.stopEvt = stopEvt
        self.lock = lock
        self.yarpInputPort = yarp.Port()
        self.dataProc = DataProcessor(motor_br_dev,lock)
        self.yarpInputPort.setReader(self.dataProc)
        
    def run(self):
        print ("MotorBrakeYarpCmdReader is starting ")
        self.yarpInputPort.open("/motorbrake/cmd:i")
        while True:
            self.stopEvt.wait()
            print ("MotorBrakeYarpCmdReader is closing...")
            self.yarpInputPort.close()
            break;
            
            
            # bottle = yarp.Bottle()
            # self.yarpInputPort.read(bottle)
            # print("I read", bottle.toString())

            #with self.lock:
            #    motor_br_data = self.motor_br_dev.setData()

                 