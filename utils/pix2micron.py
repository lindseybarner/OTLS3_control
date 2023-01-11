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
import laser.skyra as skyra
import xyz_stage.ms2000 as ms2000
import thorlabs_apt as apt
import generator.ni as generator
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
import imreg_dft as ird

def spatialCalibration(wavelengths, initial_powers):

	############# SCAN PARAMETERS #############

	# Inputs
	camX = 2048 # px
	camY = 2048 # px
	camOffset = 0 # counts
	expTime = 9.99 # msec
	binning = '1x1' # 1x1, 2x2, or 4x4
	spatial_offset = 0.04 # mm
	N = 10
	calibrations = []

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
	hcam.setACQMode("fixed_length", 1)

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

	# Set trigger properties
	#hcam.setPropertyValue("trigger_source", 'INTERNAL') # 1 (internal), 2 (external), 3 (software)
	hcam.setPropertyValue("trigger_mode", 'START') # 1 (normal), 6 (start)
	hcam.setPropertyValue("trigger_active", 'EDGE') # 1 (edge), 2 (level), 3 (syncreadout)
	hcam.setPropertyValue("trigger_polarity", 'POSITIVE') # 1 (negative), 2 (positive)
	hcam.setPropertyValue("trigger_times", 1) # only trigger once
	hcam.setPropertyValue("trigger_connector", 'BNC') # only trigger once
	hcam.setPropertyValue("trigger_delay", 0) # only trigger once

	############# SETUP XYZ STAGE #############

	xyzStage = ms2000.MS2000(baudrate = 9600, port = 'COM7')
	xyzStage.setScanF(1)
	xyzStage.setBacklash(0)
	xyzStage.setTTL(0)
	print(xyzStage)

	############### SETUP GALVO ###############
	waveform = generator.waveformGenerator(100000, round(100000*1.0*expTime/1000.0), 400, 1.6, 0)

	############### SETUP LASERS ##############
	laser = skyra.Skyra(baudrate = 115200, port = 'COM11')
	laser.turnOff(405)
	laser.turnOff(488)
	laser.turnOff(561)
	laser.turnOff(638)

	############ SETUP FILTER WHEEL ###########
	fWheel = fw102c.FW102C(baudrate = 115200, port = 'COM8')

	############### SETUP MOTOR ###############
	apt_list = apt.list_available_devices()
	apt_list = apt_list[0]
	motor = apt.Motor(apt_list[1])

	############## START SCANNING #############

	if isinstance(wavelengths,tuple) == True:
		nWavelengths = len(wavelengths)
	else:
		nWavelengths = 1

	for i in range(nWavelengths):

		if isinstance(wavelengths,tuple) == True:
			fWheel.setPosition(wavelengths[i])
		else:
			fWheel.setPosition(wavelengths)

		xyzStage.setVelocity('X',0.5)
		xyzStage.setVelocity('Y',0.5)
		xyzStage.setVelocity('Z',0.5)

		xyzStage.goAbsolute('X', 0, False)
		xyzStage.goAbsolute('Y', 0, False)
		xyzStage.goAbsolute('Z', 0, True)

		# START SCAN
		time.sleep(1)
		im = numpy.zeros((N, camX, camX), dtype = 'uint16')

		for i in range(N):

			# TURN GALVO ON
			waveform = generator.waveformGenerator(100000, round(100000*50.0*expTime/1000.0*1.5), 400, 1.6, 0)
			waveform.start()

			# TURN LASER ON
			if isinstance(wavelengths,tuple) == True:
				laser.setPower(wavelengths[i], initial_powers[i])
				laser.turnOn(wavelengths[i])
			else:
				laser.setPower(wavelengths, initial_powers)
				laser.turnOn(wavelengths)

			hcam.startAcquisition()
			time.sleep(0.01)
			[frames, dims] = hcam.getFrames()
			np_data = frames[0].getData()
			im[i] = numpy.reshape(np_data, (camY, camX))
			hcam.stopAcquisition()

			xyzStage.goAbsolute('Y', 0 + spatial_offset*(i+1), True)

		for i in range(N-1):
			tifffile.imwrite('C:\\Users\\AERB\\Desktop\\im' + str(i) + '.tif', im[i])
			result = ird.translation(im[i], im[i+1])
			tvec = result["tvec"].round(4)
			calibrations.append(round(spatial_offset*1000.0/tvec[1],3))

		# TURN LASER OFF
		if isinstance(wavelengths,tuple) == True:
			laser.turnOff(wavelengths[i])
		else:
			laser.turnOff(wavelengths)

	fWheel.shutDown()
	laser.shutDown()
	hcam.shutdown()
	
	return numpy.mean(calibrations)

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
