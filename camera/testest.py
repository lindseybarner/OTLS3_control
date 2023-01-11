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
import hamamatsu_camera as hc

hcam = hc.HamamatsuCamera(0)

# Set camera parameters.
cam_offset = 100
cam_x = 2048
cam_y = 2048
nFrames = 400
hcam.setPropertyValue("defect_correct_mode", "OFF")
hcam.setPropertyValue("exposure_time", 0.01)
hcam.setPropertyValue("subarray_hsize", cam_x)
hcam.setPropertyValue("subarray_vsize", cam_y)
hcam.setPropertyValue("binning", "1x1")
hcam.setPropertyValue("readout_speed", 2)
hcam.setACQMode("fixed_length", nFrames)

# Test image streaming using numpy.
im = numpy.zeros((nFrames, cam_y, cam_x), dtype='uint16')

hcam.startAcquisition()
time.sleep(0.01*nFrames*1.25)

cnt = 0
while cnt < nFrames:

	# Get frames.
	[frames, dims] = hcam.getFrames()

	# Save frames.
	for aframe in frames:
		print(cnt)
		np_data = aframe.getData()
		im[cnt] = numpy.reshape(np_data, (cam_y, cam_x))
		cnt += 1

hcam.stopAcquisition()

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
