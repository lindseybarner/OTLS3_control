#!/usr/bin/env python
"""
Cobolt Skyra control.

# Adam Glaser 07/19

"""
import traceback
import time
import rs232.RS232 as RS232


class Skyra(RS232.RS232):
    """
    Encapsulates communication with a Cobolt Skyra that is connected via RS-232.
    """
    def __init__(self, **kwds):
        self.live = True
        try:
            # open port
            super().__init__(**kwds)

        except Exception:
            print(traceback.format_exc())
            self.live = False
            print("Failed to connect to the Cobolt Skyra!")

    def turnOn(self, wavelength):
        """
        Turn laser ON.
        """
        position = self.wavelengthToPos(wavelength)
        self.sendCommand(str(position) + "l1")
        self.waitResponse()

    def turnOff(self, wavelength):
        """
        Turn laser OFF.
        """
        position = self.wavelengthToPos(wavelength)
        self.sendCommand(str(position) + "l0")
        self.waitResponse()

    def setPower(self, wavelength, power):
        """
        Set the laser power.
        """
        position = self.wavelengthToPos(wavelength)
        power = power/1000 # convert to W
        self.sendCommand(str(position) + "p " + str(power))
        self.waitResponse()

    def wavelengthToPos(self, wavelength):
        if wavelength == 405:
            position = 4
        elif wavelength == 488:
            position = 3
        elif wavelength == 561:
            position = 1
        elif wavelength == 638:
            position = 2
        else:
            self.live = False
            print(str(wavelength + " is not a valid wavelength!"))
        return position

if (__name__ == "__main__"):
    laser = skyra()
    laser.shutDown()


#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
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