#!/usr/bin/python
#
## @file
"""
RS232 interface to a Applied Scientific Instrumentation MS2000 stage.

Hazen 3/09
Adam Glaser 07/19
Kevin Bishop 2/22 - changed to be for Tiger controller instead.
Added set acceleration on 5/6/22 -KB
Renamed variables to refer to mm and not um (code is correct,
    but names/comments weren't) on 5/9/22 -KB

"""
import sys 
import hardware.RS232 as RS232
import time

## TIGER
#
# Applied Scientific Instrumentation tiger RS232 interface class.
#
class TIGER(RS232.RS232):

    ## __init__
    #
    # Connect to the Tiger stage at the specified port.
    #
    # @param port The RS-232 port name (e.g. "COM1").
    # @param wait_time (Optional) How long (in seconds) for a response from the stage.
    #
    def __init__(self, **kwds):

        self.mm_to_unit = 10000    #10000 means "10000 units = 1mm"
        self.unit_to_mm = 1.0/self.mm_to_unit
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        try:
            # open port
            super().__init__(**kwds)
        except:
            print("ASI Stage is not connected? Stage is not on?")

    def getCD(self):
        response = self.commWithResp("CD")
        return response

    def getBU(self):
        response = self.commWithResp("BU X")
        return response

    ## getMotorStatus
    #
    # @return True/False if the stage is moving.
    #
    def getMotorStatus(self):
        response = self.commWithResp("/")
        return response

    ## goAbsolute
    #
    # @param axis - X, Y, or Z.
    # @param pos position in mm
    #
    def goAbsolute(self, axis, pos, bwait):
        p = pos * self.mm_to_unit
        p = round(p)
        self.commWithResp("M " + axis + "=" + str(p))
        if bwait == True:
            response = self.getMotorStatus()
            while response[0] == 'B':
                response = self.getMotorStatus()

    ## goRelative
    #
    # @param x Amount to move the stage in x in mm.
    # @param y Amount to move the stage in y in mm.
    #
    def goRelative(self, axis, pos, bwait):
        p = pos * self.mm_to_unit
        p = round(p)
        self.commWithResp("R " + axis + "=" + str(p))
        if bwait == True:
            response = self.getMotorStatus()
            while response[0] == 'B':
                response = self.getMotorStatus()

    ## getPosition
    #
    # @return [stage x (mm), stage y (mm), stage z (mm)]
    #
    def getPosition(self):
        try:
            [self.x, self.y, self.z] = self.commWithResp("W X Y Z").split(" ")[1:4]
            self.x = float(self.x)*self.unit_to_mm # convert to mm
            self.y = float(self.y)*self.unit_to_mm # convert to mm
            self.z = float(self.z)*self.unit_to_mm # convert to mm
        except:
            print("Stage Error")
        return [self.x, self.y, self.z]

    ## setBacklash
    #
    # @param backlash. 0 (off) or 1 (on)
    #
    def setBacklash(self, axis, backlash):
        self.commWithResp("B " + axis + "=" + str(backlash))

    ## scan
    #
    # @param activate stage scan
    #
    def scan(self,bwait):
        self.commWithResp("SCAN")
        if bwait == True:
            response = self.getMotorStatus()
            while response[0] == 'B':
                response = self.getMotorStatus()

    ## setScanF
    #
    # @param f. 0 - RASTER, 1 - SERPENTINE
    #
    def setScanF(self, x):
        self.commWithResp("SCAN F=" + str(x))

    ## setScanR
    #
    # @param x. START (in mm)
    # @param y. STOP (in mm)
    # @param z. ENC_DIVIDE
    #
    def setScanR(self, x, y):
        x = round(x,3)
        y = round(y,3)
        self.commWithResp("SCANR X=" + str(x) + " Y=" + str(y))

    ### ****May need to be updated for F param: http://asiimaging.com/docs/products/tiger#commandscanv_nv****
    ## setScanV
    #
    # @param x. START (in mm)
    # @param y. STOP (in mm)
    # @param z. NUMBER OF LINES
    # @param f. OVERSHOOT FACTOR
    #
    def setScanV(self, x):
        x = round(x,3)
        self.commWithResp("SCANV X=" + str(x) + "Y=" + str(x) + " Z=1 F=10")
        #may need to adjust F number, it is the extra settling time in ms

    ## setTTL
    #
    # @param card. card number (1, 2, 3, etc.)
    # @param axis. X, Y, or Z.
    # @param TTL. 0 (on) or 1 (off)
    #
    def setTTL(self, card, axis, ttl):
        self.commWithResp(str(card) + "TTL " + axis + "=" + str(ttl))

    ## setPLCPreset
    #
    # @param card. card number (1, 2, 3, etc.)
    # @param preset. preset PLC code - use 52 for stage SYNC access on BNC 3
    #
    def setPLCPreset(self, card, preset):
        self.commWithResp(str(card) + "CCA X=" + str(preset))

    ## setAcceleration
    #
    # @param axis. X, Y, or Z.
    # @param accel time (ms) to reach velocity.
    #
    def setAcceleration(self, axis, accel):
        self.commWithResp("AC " + axis + "=" + str(accel))
        
    ## setVelocity
    #
    # @param axis. X, Y, or Z.
    # @param vel Maximum velocity (mm/s).
    #
    def setVelocity(self, axis, vel):
        vel = round(vel,5)
        self.commWithResp("S " + axis + "=" + str(vel))

    ## zero
    #
    # Set the current stage position as the stage zero.
    #
    def zero(self):
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
