#!/usr/bin/python
#
## @file
#
# For testing how to write 2048 x 2048 pixels at 100fps.
#
# Hazen 10/13
#

import ctypes
import ctypes.util
import numpy
import time
import tifffile as tiff
import hamamatsu_camera as hc
import RS232
import FW102C
import skyra
import ms2000
import thorlabs_apt as apt

########## SETUP CAMERA HARDWARE ##########

hcam = hc.HamamatsuCameraMR(camera_id=0)

# Set camera parameters.
cam_x = 2048 # px
cam_y = 256 # px
nFrame = 1200 # frames
cam_offset = 0 # counts
expTime = 1.249 # msec
binFactor = '1x1' # 1x1, 2x2, or 4x4

# Set aquisition mode
hcam.setACQMode("fixed_length", nFrame)

# Set camera properties
hcam.setPropertyValue("defect_correct_mode", "ON") # keep defect mode on
hcam.setPropertyValue("readout_speed", 2) # 1 or 2. 2 is fastest mode
hcam.setPropertyValue("exposure_time", expTime/1000) # convert from msec to sec
hcam.setPropertyValue("subarray_hsize", cam_x)
hcam.setPropertyValue("subarray_vsize", cam_y)
hcam.setPropertyValue("binning", binFactor)

# Set trigger properties
hcam.setPropertyValue("trigger_source", 1) # 1 (internal), 2 (external), 3 (software)
hcam.setPropertyValue("trigger_mode", 6) # 1 (normal), 6 (start)
hcam.setPropertyValue("trigger_active", 1) # 1 (edge), 2 (level), 3 (syncreadout)
hcam.setPropertyValue("trigger_polarity", 2) # 1 (negative), 2 (positive)
hcam.setPropertyValue("trigger_times", 1) # only trigger once

####### SETUP FILTER WHEEL HARDWARE #######

fwheel = FW102C.FW102C(baudrate = 115200, port = 'COM8')
print(fwheel)

########## SETUP LASER HARDWARE ###########

laser = skyra.Skyra(baudrate = 115200, port = 'COM11')
print(laser)

############# SETUP XYZ STAGE #############

xyzstage = ms2000.MS2000(baudrate = 9600, port = 'COM7')
print(xyzstage)

############# SETUP APT MOTOR #############

apt_list = apt.list_available_devices()
apt_list = apt_list[0]
motor = apt.Motor(apt_list[1])
apt.core._cleanup()
print(motor)

# Test image streaming using numpy.

im = numpy.zeros((nFrame, cam_y, cam_x), dtype='uint16')

if 1:

    hcam.startAcquisition()
    # pauseTime = 1.2*(nFrame*expTime)
    # time.sleep(pauseTime)

    # [frames, dims] = hcam.getFrames()

    # i=0
    # print(len(frames))
    # for aFrame in frames:
    #     print (i)
    #     np_data = aFrame.getData()-cam_offset
    #     im[i] = numpy.reshape(np_data, (cam_x, cam_y))
    #     i = i+1

    for i in range(nFrame):
    	
        print(i)
        # Get frames.
        [frames, dims] = hcam.getFrames()

        # Save frames.
        j=0
        for aframe in frames:
            np_data = aframe.getData()-cam_offset
            im[i] = numpy.reshape(np_data, (cam_y, cam_x))
            j = j+1

    tiff.imsave('y:/test.tiff', im)
    hcam.stopAcquisition()
    hcam.shutdown()
#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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
