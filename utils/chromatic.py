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
from scipy.interpolate import UnivariateSpline

def FWHM(x, y):

    y = y / y.max()
    N = len(y)
    lev50 = 0.5
    if y[0] < lev50:
        center_ind = numpy.argmax(y)
        pol = 1
    else:
        center_ind = numpy.argmin(y)
        pol = -1

    i = 1
    while numpy.sign(y[i] - lev50) == numpy.sign(y[i-1] - lev50):
        i = i+1
    interp = (lev50 - y[i-1])/(y[i] - y[i-1])
    tlead = x[i-1] + interp*(x[i] - x[i-1])

    i = center_ind + 1
    while (numpy.sign(y[i] - lev50) == numpy.sign(y[i-1] - lev50)) and (i <= N-2):
        i = i+1

    if i != N-1:
        Ptype = 1
        interp = (lev50 - y[i-1])/(y[i] - y[i-1])
        ttrail = x[i-1] + interp*(x[i] - x[i-1])
        width = ttrail - tlead
    else:
        Ptype = 2
        ttrail = 100
        width = 100 # make large value

    if width == 0:
        width = 100 # make large value

    return width

def colorCorrection(wavelengths, initial_powers, yoff_previous):

	############# SCAN PARAMETERS #############

	# Inputs
	camX = 2048 # px
	camY = 2048 # px
	camOffset = 0 # counts
	expTime = 9.99 # msec
	binning = '4x4' # 1x1, 2x2, or 4x4
	motor_min = 2.0
	motor_max = 10.0
	motor_list = numpy.arange(motor_min, motor_max, 0.1)

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
	waveform = generator.waveformGenerator(100000, round(100000*len(motor_list)*expTime/1000.0), 400, 0, 0)

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

	fWheel.setPosition(wavelengths)

	xyzStage.setVelocity('X',0.5)
	xyzStage.setVelocity('Y',0.5)
	xyzStage.setVelocity('Z',0.5)

	xPos = 0
	yPos = -1.40+yoff_previous
	zPos = 0.2

	xyzStage.goAbsolute('X', xPos, False)
	xyzStage.goAbsolute('Y', yPos, False)
	xyzStage.goAbsolute('Z', zPos, True)

	# TURN GALVO ON
	waveform = generator.waveformGenerator(100000, round(100000*len(motor_list)*expTime/1000.0*1.5), 400, 0, 0)
	waveform.start()

	# TURN LASER ON
	laser.setPower(wavelengths, initial_powers)
	laser.turnOn(wavelengths)

	# START SCAN
	time.sleep(1)
	im = numpy.zeros((len(motor_list), camY, camX), dtype = 'uint16')
	for j in range(len(motor_list)):
		motor.move_to(motor_list[j], blocking = True)
		hcam.startAcquisition()
		time.sleep(0.1)
		[frames, dims] = hcam.getFrames()
		np_data = frames[0].getData()
		im[j] = scipy.ndimage.median_filter(numpy.reshape(np_data, (camY, camX)), 3)
		hcam.stopAcquisition()

	bkg = (numpy.median(im[:,0:100]) + numpy.median(im[:,411:511]))/2.0
	im = abs(im - bkg)
	im = im.astype('uint16')

	# TURN LASER OFF
	laser.setPower(wavelengths, 1.0)
	laser.turnOff(wavelengths)

	sz=im.shape[0]
	mean_idx = numpy.zeros(im.shape[2])
	for j in range(im.shape[0]):
	    im_temp=im[j]
	    dx = numpy.zeros(im_temp.shape[0])
	    for k in range(im_temp.shape[0]):
	        lp=im_temp[k,:]
	        x = numpy.arange(-im_temp.shape[1]/2, im_temp.shape[1]/2, 1)
	        dx[k] = FWHM(x,lp)

	    dx = dx/numpy.nanmin(dx) - math.sqrt(2)
	    idx = numpy.where(dx < 0)
	    min_idx = numpy.min(idx)
	    max_idx = numpy.max(idx)
	    mean_idx[j] = round((min_idx + max_idx)/2.0)

	mean_idx = abs(mean_idx - im.shape[1]/2)
	final_idx = numpy.where(mean_idx == min(mean_idx))
	optimal = motor_list[final_idx];
	motor_positions = (round(numpy.mean(optimal),3))
	
	fWheel.shutDown()
	laser.shutDown()
	hcam.shutdown()

	return(motor_positions)

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
