#!/usr/bin/python
#
## @file
"""
RS232 interface to a Applied Scientific Instrumentation MS2000 stage.

Hazen 3/09
Adam Glaser 07/19\

"""

import sys
import time
import rs232.RS232 as RS232
import laser.obis as obis #added LB 1-3-20 so we can turn laser off right after stage stops scanning
import laser.sapphire as sapphire
import time

## MS2000
#
# Applied Scientific Instrumentation MS2000 RS232 interface class.
#
class MS2000(RS232.RS232):

    ## __init__
    #
    # Connect to the MS2000 stage at the specified port.
    #
    # @param port The RS-232 port name (e.g. "COM1").
    # @param wait_time (Optional) How long (in seconds) for a response from the stage.
    #
    def __init__(self, **kwds):

        self.live = True
        self.um_to_unit = 10000
        self.unit_to_um = 1.0/self.um_to_unit
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        try:
            # open port
            super().__init__(**kwds)
        except:
            self.live = False
            print("ASI Stage is not connected? Stage is not on?")

    ## getMotorStatus
    #
    # @return True/False if the stage is moving.
    #
    def getMotorStatus(self):
        response = self.commWithResp("/")
        return response

    ## getStatus
    #
    # @return True/False if we are actually connected to the stage.
    #
    def getStatus(self):
        return self.live

    ## goAbsolute
    #
    # @param axis - X, Y, or Z.
    # @param pos position.
    #
    def goAbsolute(self, axis, pos, bwait):
        if self.live:
            p = pos * self.um_to_unit
            p = round(p)
            self.commWithResp("M " + axis + "=" + str(p))
            if bwait == True:
                response = self.getMotorStatus()
                while response[0] == 'B':
                    response = self.getMotorStatus()

    ## goRelative
    #
    # @param x Amount to move the stage in x in um.
    # @param y Amount to move the stage in y in um.
    #
    def goRelative(self, axis, pos, bwait):
        if self.live:
            p = pos * self.um_to_unit
            p = round(p)
            self.commWithResp("R " + axis + "=" + str(p))
            if bwait == True:
                response = self.getMotorStatus()
                while response[0] == 'B':
                    response = self.getMotorStatus()
    ## jog
    #
    # @param x_speed Speed to jog the stage in x in um/s.
    # @param y_speed Speed to jog the stage in y in um/s.
    #
    def jog(self, x_speed, y_speed):
        pass
#        if self.live:
#            vx = x_speed * 0.001
#            vy = y_speed * 0.001
#            self.commWithResp("S X=" + str(vx) + " Y=" + str(vy))

    ## joystickOnOff
    #
    # @param on True/False enable/disable the joystick.
    #
    def joystickOnOff(self, on):
        pass
        #if self.live:
        #    if on:
        #        self.commWithResp("!joy 2")
        #    else:
        #        self.commWithResp("!joy 0")

    ## getPosition
    #
    # @return [stage x (um), stage y (um), stage z (um)]
    #
    def getPosition(self):
        if self.live:
            try:
                [self.x, self.y, self.z] = self.commWithResp("W X Y Z").split(" ")[1:4]
                self.x = float(self.x)*self.unit_to_um # convert to mm
                self.y = float(self.y)*self.unit_to_um # convert to mm
                self.z = float(self.z)*self.unit_to_um # convert to mm
            except:
                print("Stage Error")
            return [self.x, self.y, self.z]
        else:
            return [0.0, 0.0, 0.0]

    ## setBacklash
    #
    # @param backlash. 0 (off) or 1 (on)
    #
    def setBacklash(self, backlash):
        if self.live:
            self.commWithResp("B X=" + str(backlash))

    ## scan
    #
    # @param activate stage scan
    # #
    def scan(self,bwait,laser,xPos):
        self.laser = laser #modified LB 1-3-20 added this whole line
        if self.live:
            self.commWithResp("SCAN F = 1")
            self.commWithResp("SCAN")
            print('stage scanning') #added LB 1-3-19
            if bwait == True:
                response = self.getMotorStatus()
                while response[0] == 'B':
                    response = self.getMotorStatus()
            while self.getMotorStatus()[0] == 'B':
                pass
                #print('busy')
            if self.getMotorStatus()[0] == 'N':
                print('done scanning, laser off')
                laser.turnOff() #this turns laser off right after scan, as opposed to after frames finish buffering (prevents b)
                time.sleep(5)
                self.goAbsolute('X',xPos,False)


#for testing
    # def scan(self,bwait):
    #     if self.live:
    #         self.commWithResp("SCANF = 1")
    #         self.commWithResp("SCAN")
    #         if bwait == True:
    #             response = self.getMotorStatus()
    #             while response[0] == 'B':
    #                 response = self.getMotorStatus()

    # def laser_FastOff(laser): #added LB 1-3-20
    #     laser.turnOff()
    #     print('laser enabled')





    ## setScanR
    #
    # @param x. START
    # @param y. STOP
    # @param z. ENC_DIVIDE

    ## setScanF
    #
    # @param scan_f. 0 (raster) or 1 (serpentine)
    #
    def setScanF(self, scan_f):
        if self.live:
            self.commWithResp("SCANF =" + str(scan_f))

    ## setScanR
    #
    # @param x. START
    # @param y. STOP
    # @param z. ENC_DIVIDE
    #
    def setScanR(self, x, y): #set scan range/positions
        if self.live:
            x = round(x,3)
            y = round(y,3)
            self.commWithResp("SCANR X=" + str(x) + " Y=" + str(y))

    ## setScanV
    #
    # @param x. START
    # @param y. STOP
    # @param z. NUMBER OF LINES
    # @param f. OVERSHOOT FACTOR
    #
    def setScanV(self, x): #this sets a position not velocity
        if self.live:
            x = round(x,3)
            self.commWithResp("SCANV X=" + str(x))

    ## setTTL
    #
    # @param scan_f. 0 (on) or 1 (off)
    #
    def setTTL(self, ttl):
        if self.live:
            self.commWithResp("TTL X=" + str(ttl))

    ## setVelocity
    #
    # @param axis - X, Y, or Z.
    # @param vel Maximum velocity.
    #
    def setVelocity(self, axis, vel):
        if self.live:
            vel = round(vel,5) #rounds to 5 decimals
            self.commWithResp("S " + axis + "=" + str(vel))

    ## zero
    #
    # Set the current stage position as the stage zero.
    #
    def zero(self):
        if self.live:
            self.commWithResp("Z")

#
# The MIT License
#
# Copyright (c) 2014 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
