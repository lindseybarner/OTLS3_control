#!/usr/bin/env python
"""
This script is used for camera calibration. It records the sum of x and 
the sum of x*x for every pixel in every frame.

Hazen 10/13
"""

import numpy
import sys
import time
import hamamatsu_camera as hc
import os
import shutil
import h5py

hcam = hc.HamamatsuCameraMR(camera_id = 0)

# Set camera parameters.
binFactor = 1
nFrames = 35715
camY = 256
camX = 2048
save_dir = 'test'
idx = 0

hcam.setPropertyValue("defect_correct_mode", "OFF")
hcam.setPropertyValue("readout_speed", 2)

hcam.setPropertyValue("defect_correct_mode", "ON") # keep defect mode on
hcam.setPropertyValue("readout_speed", 2) # 1 or 2. 2 is fastest mode
hcam.setPropertyValue("exposure_time", 4.99/1000.0) # convert from msec to sec
hcam.setPropertyValue("subarray_hsize", 2048)
hcam.setPropertyValue("subarray_vsize", 256)
hcam.setPropertyValue("subarray_vpos", 1024-256/2)
hcam.setPropertyValue("binning", binFactor)
hcam.setACQMode("fixed_length", nFrames)

hcam.startAcquisition()

# CAPTURE IMAGES
count_old = 0
count_new = 0
count = 0
im = numpy.zeros((nFrames, camY, camX), dtype = 'uint16')

if os.path.exists('Y:\\' + save_dir):
    shutil.rmtree('Y:\\' + save_dir, ignore_errors=True)
    time.sleep(1)
    os.makedirs('Y:\\' + save_dir)
    dest = 'Y:\\' + save_dir + '\\data.h5'
    f = h5py.File(dest,'a')
    imgShape = (nFrames, camY, camX)
    chunkSize1 = 256/binFactor
    chunkSize2 = 32/binFactor
    chunkSize3 = 256/binFactor

data = f.require_dataset('/t00000/s' + str(idx).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, chunkSize2, chunkSize3), dtype = 'int16', shape = imgShape, compression = 32016, compression_opts=(round(2*1000), 1, round(2.1845*1000), 0, round(1.6*1000)))

while count < nFrames-1:
    time.sleep(0.01)
    # Get frames.
    [frames, dims] = hcam.getFrames()
    count_old = count
    # Save frames.
    for aframe in frames:
        np_data = aframe.getData()
        #im.append(numpy.reshape(np_data, (camY, camX)))
        im[count] = numpy.reshape(np_data, (camY, camX))
        count += 1
    count_new = count
    data[count_old:count_new] = im[count_old:count_new]
    print(count_new)

hcam.stopAcquisition()
hcam.shutdown()
f.close()


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
