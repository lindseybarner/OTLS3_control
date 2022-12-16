#!/usr/bin/python
#
## @file
"""
RS232 interface to a Applied Scientific Instrumentation MS2000 stage.

Hazen 3/09
Adam Glaser 07/19

"""
import sys 
import hardware.RS232 as RS232
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

        self.um_to_unit = 10000
        self.unit_to_um = 1.0/self.um_to_unit
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        try:
            # open port
            super().__init__(**kwds)
        except:
            print("ASI Stage is not connected? Stage is not on?")

    def getAcceleration(self):
        response = self.commWithResp("AC X? Y? Z?")
        return response

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
    # @param pos position.
    #
    def goAbsolute(self, axis, pos, bwait):
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
        p = pos * self.um_to_unit
        p = round(p)
        self.commWithResp("R " + axis + "=" + str(p))
        if bwait == True:
            response = self.getMotorStatus()
            while response[0] == 'B':
                response = self.getMotorStatus()

    ## getPosition
    #
    # @return [stage x (um), stage y (um), stage z (um)]
    #
    def getPosition(self):
        try:
            [self.x, self.y, self.z] = self.commWithResp("W X Y Z").split(" ")[1:4]
            self.x = float(self.x)*self.unit_to_um # convert to mm
            self.y = float(self.y)*self.unit_to_um # convert to mm
            self.z = float(self.z)*self.unit_to_um # convert to mm
        except:
            print("Stage Error")
            raise Exception('Stage Error - restart code')
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
    # @param x. START
    # @param y. STOP
    # @param z. ENC_DIVIDE
    #
    def setScanR(self, x, y):
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
    def setScanV(self, x):
        x = round(x,3)
        self.commWithResp("SCANV X=" + str(x) + "Y=" + str(x) + " Z=1 F=2")

    ## setTTL
    #
    # @param axis. X, Y, or Z.
    # @param TTL. 0 (on) or 1 (off)
    #
    def setTTL(self, axis, ttl):
        self.commWithResp("TTL " + axis + "=" + str(ttl))

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
    # @param vel Maximum velocity.
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
