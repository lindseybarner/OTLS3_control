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

hcam = hc.HamamatsuCameraMR(camera_id=0)
print(hcam.getCameraProperties())
print(hcam.getPropertyRange('trigger_source'))
print(hcam.getPropertyText('trigger_source'))

print(hcam.getPropertyRange('trigger_mode'))
print(hcam.getPropertyText('trigger_mode'))

print(hcam.getPropertyRange('trigger_active'))
print(hcam.getPropertyText('trigger_active'))

print(hcam.getPropertyRange('trigger_polarity'))
print(hcam.getPropertyText('trigger_polarity'))

print(hcam.getPropertyRange('trigger_times'))
print(hcam.getPropertyText('trigger_times'))


# Set camera parameters.
# cam_x = 2048
# cam_y = 2048
# nFrame = 1200
# cam_offset= 0
# expTime = 0.01
# hcam.setPropertyValue("defect_correct_mode", "OFF")
# hcam.setPropertyValue("exposure_time", expTime)
# hcam.setPropertyValue("subarray_hsize", cam_x)
# hcam.setPropertyValue("subarray_vsize", cam_y)
# hcam.setPropertyValue("binning", "1x1")
# hcam.setPropertyValue("readout_speed", 2)
# hcam.setACQMode("fixed_length", nFrame)

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