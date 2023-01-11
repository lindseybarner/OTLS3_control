#!/usr/bin/python

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

def findBounds(wavelengths, motor_positions, initial_powers, sampling, expTime_in, binFactor_in, yoff_previous):

	############# SCAN PARAMETERS #############

	# Inputs
	attenuations = 1.5 # mm^-1
	xLength = 30.0 # mm
	yLength = 0.8 # mm
	zLength = 0.07 # mm
	xWidth = 10 # microns
	yWidth = 0.8 # mm
	zWidth = 0.07 # mm
	camX = 2048 # px
	camY = 2048 # px
	camOffset = 0 # counts
	expTime = 9.99 # msec
	binning = '4x4' # 1x1, 2x2, or 4x4
	xOffset = 0.035 # mm

	# Calculate additional inputs
	nFrames = math.ceil(xLength/(xWidth/1000))
	yTiles = math.ceil(yLength/yWidth)
	zTiles = math.ceil(zLength/zWidth)
	scanSpeed = xWidth/(1.0/(1.0/(expTime/1000.0))*1000)
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
	waveform = generator.waveformGenerator(100000, round(100000*nFrames*expTime/1000.0), 400, 1.4, 0)

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

	motor.move_to(motor_positions)

	for j in range(zTiles):
		for k in range(yTiles):

			# GO TO INITIAL POSITIONS

			xyzStage.setVelocity('X',0.5)
			xyzStage.setVelocity('Y',0.5)
			xyzStage.setVelocity('Z',0.5)

			xPos = xLength/2.0
			yPos = -yLength/2.0+k*yWidth+yWidth/2.0+yoff_previous
			zPos = j*zWidth

			xyzStage.goAbsolute('X', -xPos-xOffset, False)
			xyzStage.goAbsolute('Y', yPos, False)
			xyzStage.goAbsolute('Z', zPos, True)

			xyzStage.setVelocity('X',scanSpeed)
			xyzStage.setScanR(-xPos, xPos)
			xyzStage.setScanV(yPos)

			# INITIALIZE VARIABLES
			im = numpy.zeros((nFrames, camX, camX), dtype = 'uint16')

			# TURN GALVO ON
			waveform = generator.waveformGenerator(100000, round(100000*nFrames*expTime/1000.0*1.5), 400, 1.4, 0)
			waveform.start()

			# TURN LASER ON
			laser.setPower(wavelengths, initial_powers*math.exp(j*zWidth/attenuations))
			laser.turnOn(wavelengths)

			# START SCAN
			hcam.startAcquisition()
			xyzStage.scan(False)

			# CAPTURE IMAGES
			count_old = 0
			count_new = 0
			count = 0

			while count < nFrames:
				time.sleep(0.01)
				# Get frames.
				[frames, dims] = hcam.getFrames()
				count_old = count
				# Save frames.
				for aframe in frames:
					np_data = aframe.getData()
					im[count] = numpy.reshape(np_data, (camY, camX))
					count += 1
				count_new = count

			# TURN LASER OFF
			laser.setPower(wavelengths, 1.0)
			laser.turnOff(wavelengths)

			hcam.stopAcquisition()
			gc.collect()

			# CALCULATE BOUNDS
			im = im.transpose((1,2,0))
			bkgLevel = 50*binFactor*binFactor
			ind=numpy.where(im>bkgLevel);
			m1=numpy.mean(im[ind]);
			S=numpy.sort(im, axis = None)
			meanInt=S[round(numpy.size(S)*0.95)];
			se = numpy.ones((41,41), numpy.uint16)

			# YZ
			YZ=numpy.mean(im, axis = 2)
			YZseg=YZ;
			YZseg[numpy.where(YZseg<=m1)]=0
			YZseg[numpy.where(YZseg>m1)]=1
			YZseg=cv2.dilate(YZseg, se, iterations = 0)
			YZseg=cv2.erode(YZseg, se, iterations = 0)

			sy=numpy.mean(YZseg, axis = 0)
			ind=numpy.where(sy>0.12)
			boundy=(numpy.min(ind), numpy.max(ind))
			if boundy[0]==0:
				boundy=(numpy.max(ind)-334, numpy.max(ind))
			elif boundy[1]==511:
				boundy=(numpy.min(ind), numpy.min(ind)+334)
			else:
				boundy=boundy;

			boundy=numpy.mean(boundy)

			norm=numpy.sum(YZseg, axis = 0)
			ind=numpy.where(norm==0)
			YZseg_temp=YZseg;
			YZseg_temp[:,ind]=numpy.NaN

			sz=numpy.nanmean(YZseg_temp, axis = 1)
			ind=numpy.where(sz>0.5)
			boundz=(numpy.min(ind), numpy.max(ind))
			boundz=boundz[1]

			# XZ
			XZ=numpy.squeeze(numpy.mean(im, axis = 1))
			XZseg=XZ;
			XZseg[numpy.where(XZseg<=m1)]=0
			XZseg[numpy.where(XZseg>m1)]=1
			XZseg=cv2.dilate(XZseg, se, iterations = 0);
			XZseg=cv2.erode(XZseg, se, iterations = 0);

			sx=numpy.mean(XZseg, axis = 0)
			ind=numpy.where(sx>0.12)
			boundx=(numpy.min(ind), numpy.max(ind))

			norm=numpy.sum(XZseg, axis = 0)
			ind=numpy.where(norm==0)
			XZseg_temp=XZseg
			XZseg_temp[:,ind]=numpy.NaN

			sz=numpy.nanmean(XZseg_temp, axis = 1)
			ind=numpy.where(sz>0.5)
			boundz_2=(numpy.min(ind), numpy.max(ind))
			boundz_2=boundz_2[1]

			# XY
			XY=numpy.squeeze(numpy.mean(im, axis = 0))
			XYseg=XY;
			XYseg[numpy.where(XYseg<=m1)]=0
			XYseg[numpy.where(XYseg>m1)]=1
			XYseg=cv2.dilate(XYseg, se, iterations = 0);
			XYseg=cv2.erode(XYseg, se, iterations = 0);

			sx=numpy.mean(XYseg, axis = 0);
			ind=numpy.where(sx>0.2);
			boundx_2=(numpy.min(ind), numpy.max(ind))

			norm=numpy.sum(XYseg, axis = 0)
			ind=numpy.where(norm==0)
			XYseg_temp=XYseg
			XYseg_temp[:,ind]=numpy.NaN

			sy=numpy.nanmean(XYseg_temp, axis = 1)
			ind=numpy.where(sy>0.5)
			boundy_2=(numpy.min(ind), numpy.max(ind))

			if boundy_2[0]==0:
				boundy_2=(numpy.max(ind)-334, numpy.max(ind));
			elif boundy_2[1]==511:
				boundy_2=(numpy.min(ind), numpy.min(ind)+334);
			else:
				boundy_2=boundy_2;

			boundy_2=numpy.mean(boundy_2);

			# OUTPUT
			pix2um=sampling*binFactor;
			yoff=-(im.shape[1]/2-round((boundy+boundy_2)/2))*pix2um/1000; #mm
			zoff=(im.shape[0]/2-round((boundz+boundz_2)/2))*pix2um/math.sqrt(2)/1000; #mm
			xoff=-(im.shape[2]/2-((boundx[0]+boundx_2[0])/2+(boundx[1]+boundx_2[1])/2)/2)*xWidth/1000; #mm
			length=((boundx[1]+boundx_2[1])/2-(boundx[0]+boundx_2[0])/2)*xWidth/1000; #mm
			power=initial_powers*4000/meanInt*(expTime/expTime_in)*(binFactor/binFactor_in)

	fWheel.shutDown()
	laser.shutDown()
	hcam.shutdown()

	return(xoff, yoff, zoff, length, power)

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
