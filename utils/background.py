#!/usr/bin/python
#

import ctypes
import ctypes.util
import numpy
import time
import math
import camera.hamamatsu_camera as hc
import rs232.RS232 as RS232
import filter_wheel.fw102c as fw102c
# import laser.skyra as skyra
import xyz_stage.ms2000 as ms2000
# import thorlabs_apt as apt
# import generator.ni as generator
import h5py
import warnings
import os.path
import errno
import sys
import scipy.ndimage
import h5py
import warnings
import gc
import nidaqmx
import os
import os.path
from os import path
import shutil
import tifffile
import cv2

def backgroundSubtract(camX, camY, expTime, binning):

	nFrames = 1000

	# Calculate additional inputs
	if binning == '1x1':
		binFactor = 1
	elif binning == '2x2':
		binFactor = 2
	elif binning == '4x4':
		binFactor = 4
	else:
		binFactor = 1

	############# SETUP CAMERA #############
	hcam = hc.HamamatsuCameraMR(camera_id=0)
	print(hcam)
	# Set aquisition mode
	hcam.setACQMode("fixed_length", nFrames)

	# Set camera properties
	hcam.setPropertyValue("defect_correct_mode", "ON") # keep defect mode on
	hcam.setPropertyValue("readout_speed", 2) # 1 or 2. 2 is fastest mode
	hcam.setPropertyValue("exposure_time", expTime/1000.0) # convert from msec to sec
	hcam.setPropertyValue("subarray_hsize", camX)
	hcam.setPropertyValue("subarray_vsize", camY)
	hcam.setPropertyValue("subarray_vpos", 1024-camY/2)
	hcam.setPropertyValue("binning", binning)

	# Adjust for binning factor
	camY = int(camY/binFactor)
	camX = int(camX/binFactor)

	im = numpy.zeros((nFrames, camY, camX), dtype = 'uint16')

	hcam.startAcquisition()
	count = 0
	while count < nFrames-1:
		time.sleep(0.01)
		# Get frames.
		[frames, dims] = hcam.getFrames()
		# Save frames.
		for aframe in frames:
			np_data = aframe.getData()
			im[count] = numpy.reshape(np_data, (camY, camX))
			count += 1

	hcam.stopAcquisition()
	hcam.shutdown()
	
	bkg = numpy.median(im, axis = 0)

	return(bkg)

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
