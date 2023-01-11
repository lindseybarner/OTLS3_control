#!/usr/bin/python
#

# import imagej
# ij = imagej.init('C:\\Users\\AERB\\Documents\\Fiji.app', headless = False)
# from imglyb import util

# from jnius import autoclass
# spimData = autoclass('bdv.spimdata.SpimDataMinimal')
# spimXML = autoclass('bdv.spimdata.XmlIoSpimDataMinimal')
# bdvWindow = autoclass('bdv.util.BdvFunctions')

import ctypes
import ctypes.util
import numpy
import time
import math
import camera.hamamatsu_camera as hc
import rs232.RS232 as RS232
import filter_wheel.fw102c_LB as fw102c_LB
import laser.obis as obis
import xyz_stage.ms2000 as ms2000
# import thorlabs_apt as apt
# import generator.ni as generator
# import utils.findbounds as findbounds
import utils.utils as utils
import utils.background as background
import h5py
import warnings
import os
import os.path
import errno
import sys
import scipy.ndimage
import warnings
import gc
import nidaqmx
from os import path
import shutil
import logging
import tifffile

def scan3D(drive, save_dir, xoff, yoff, zoff, xLength, yLength, zLength, xWidth, yWidth, zWidth, yStitchOverlay, zStitchOverlay, camY, camX, expTime, binning, wavelengths, initial_powers, motor_positions, attenuations, camOffset, flatField = 0, vis = 0):

	if binning == '1x1':
		binFactor = 1
	elif binning == '2x2':
		binFactor = 2
	elif binning == '4x4':
		binFactor = 4
	else:
		binFactor = 1

	if wavelengths.size > 1:
		nWavelengths = len(wavelengths)
	else:
		nWavelengths = 1

	############# GET BACKGROUND ############

	bkg = background.backgroundSubtract(camX, camY, expTime, binning) - 100*binFactor*binFactor
	#print('camera background = ' + str(bkg))

	############# SETUP CAMERA #############

	hcam = hc.HamamatsuCameraMR(camera_id=0)
	print(hcam)

	# Set camera properties
	hcam.setPropertyValue("defect_correct_mode", "OFF") # keep defect mode on
	hcam.setPropertyValue("readout_speed", 2) # 1 or 2. 2 is fastest mode
	hcam.setPropertyValue("exposure_time", expTime/1000.0) # convert from msec to sec
	hcam.setPropertyValue("subarray_hsize", camX)
	hcam.setPropertyValue("subarray_vsize", camY)
	hcam.setPropertyValue("subarray_vpos", 1024-camY/2)
	hcam.setPropertyValue("binning", binFactor)

	# Set trigger properties
	hcam.setPropertyValue("trigger_source", 'INTERNAL') # 1 (internal), 2 (external), 3 (software)
	hcam.setPropertyValue("trigger_mode", 'START') # 1 (normal), 6 (start)
	hcam.setPropertyValue("trigger_active", 'EDGE') # 1 (edge), 2 (level), 3 (syncreadout)
	hcam.setPropertyValue("trigger_polarity", 'POSITIVE') # 1 (negative), 2 (positive)

	# Adjust for binning factor
	xWidth = xWidth*binFactor
	camY = int(camY/binFactor)
	camX = int(camX/binFactor)
	nFrames = int(round(xLength/(xWidth/1000))) #number of frames in X direction
	#nFrames = 2048
	yTiles = int(round(yLength/yWidth))
	zTiles = int(round(zLength/zWidth))
	scanSpeed = xWidth/expTime #um/ms or mm/sec # xWidth/(1.0/(1.0/(expTime/1000.0))*1000) LB modified to be simpler 11-22-19

	print('number of frames in X direction = ' + str(nFrames))
	print('number of tiles in Y direction = ' + str(yTiles))
	print('number of tiles in Z direction = ' + str(zTiles))

	# Set aquisition mode
	hcam.setACQMode("fixed_length", nFrames)
		
	############# SETUP XYZ STAGE #############

	xyzStage = ms2000.MS2000(baudrate = 9600, port = 'COM5')
	xyzStage.setScanF(1)
	xyzStage.setBacklash(0)
	xyzStage.setTTL(0)
	initialPos = xyzStage.getPosition()
	print(xyzStage)


	############ SETUP FILTER WHEEL ###########

	fWheel = fw102c_LB.FW102C(baudrate = 115200, port = 'COM6')


	########## PREPARE FOR SCANNING ###########

	if os.path.exists(drive + ':\\' + save_dir):
		userinput = input('this file directory already exists! permanently delete? [y/n]')
		if userinput == 'y':
			shutil.rmtree(drive + ':\\' + save_dir, ignore_errors=True)
		if userinput== 'n':
			sys.exit('--Terminating-- re-name write directory and try again')

		
	time.sleep(1)
	os.makedirs(drive + ':\\' + save_dir)
	logging.basicConfig(filename=(drive + ':\\' + save_dir + '\\log.txt'))
	dest = drive + ':\\' + save_dir + '\\data.h5'

	#save a copy of executed python files to drive for record
	shutil.copyfile('lsm5X_LB_run.py', drive + ':\\' + save_dir + '\\lsm5X_LB_run.py')
	shutil.copyfile('lsm20X_LB_run.py', drive + ':\\' + save_dir + '\\lsm20X_LB_run.py')
	shutil.copyfile('lsmfx_LB.py', drive + ':\\' + save_dir + '\\lsmfx_LB.py')


	imgShape = (nFrames, camY, camX) 
	chunkSize1 = 256/binFactor
	chunkSize2 = 32/binFactor #for Z (256px) direction
	chunkSize3 = 256/binFactor
	write_threads = []
	im = numpy.zeros((nFrames, camY, camX), dtype = 'uint16') #initialize: "X" (scan) direction, Z (256px) direction, Y direction

	print('Specimen name: ' + save_dir)
	print('x offset: ' + str(xoff) + ' mm')
	print('y offset: ' + str(yoff)+ ' mm')
	print('z offset: ' + str(zoff)+ ' mm')
	print('length: ' + str(xLength)+ ' mm')
	# print('638 nm power: ' + str(initial_powers[0])+ ' mW')
	# print('561 nm power: ' + str(initial_powers[1])+ ' mW')

	############## START SCANNING #############
	
	f = h5py.File(dest,'a')
	

	for j in range(zTiles): 
		for k in range(yTiles): 
			for i in range(nWavelengths):

				# ############### SETUP LASERS ##############
				if wavelengths[i] == 660: ## added LB 1-6-20. i have separate lasers for different colors so this code is different than adam's
					laser = obis.Obis(baudrate = 9600, port = 'COM4')
				if wavelengths[i] == 488:
					laser = obis.Obis(baudrate = 9600, port = 'COM8')
					#userinput = input('change Y galvo offset to -0.65V before proceeding to 488nm. hit enter when done')


				#xyzStage.laser_FastOff_enable() #added LB 1-3-20

				if wavelengths.size > 1:
					fWheel.setPosition(wavelengths[i])
				else:
					fWheel.setPosition(wavelengths[i])

				# GET TILE NUMBER
				idx = k+j*yTiles+i*yTiles*zTiles
				idx_tile = k+j*yTiles
				idx_channel = i

				# GET NAME FOR NEW VISUALIZATION FILE
				if idx == 0:
					dest_vis = drive + ':\\' + save_dir + '\\vis' + str(idx) + '.h5'
				else:
					dest_vis = drive + ':\\' + save_dir + '\\vis' + str(idx) + '.h5'
					dest_vis_prev = drive + ':\\' + save_dir + '\\vis' + str(idx-1) + '.h5'

				# INITIALIZE H5 FILE VARIABLES
				if idx == 0:
					tgroup = f.create_group('/t00000')
				resgroup = f.create_group('/t00000/s' + str(idx).zfill(2) + '/' + str(0))
				data = f.require_dataset('/t00000/s' + str(idx).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, chunkSize2, chunkSize3), dtype = 'int16', shape = imgShape, compression = 32016, compression_opts=(round(2*1000), 1, round(2.1845*1000), 0, round(1.6*1000)))
				#on lsfmx.py file Adam sent 11/2019, the following line was commented but the above line was not. line above throws an error for compression number 32016
				#data = f.require_dataset('/t00000/s' + str(idx).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, chunkSize2, chunkSize3), dtype = 'int16', shape = imgShape)


				# GO TO INITIAL POSITIONS
				xyzStage.setVelocity('X',0.5) #
				xyzStage.setVelocity('Y',0.5) #
				xyzStage.setVelocity('Z',0.5) 

				xPos = xLength/2.0 - xoff
				yPos = -yLength/2.0+k*yWidth+yWidth/2.0 + yoff
				zPos = j*zWidth + zoff
				print('Starting tile ' + str(idx+1) + '/' + str(zTiles*yTiles*nWavelengths)) #LB modified for indexing
				ts = time.gmtime()
				print(time.strftime("%x %X", ts))
				print('move x position to: ' + str(-xPos)+ ' mm') #modified LB 11-17-19, used to be str(-xPos-.035)
				print('move y position to: ' + str(yPos)+ ' mm')
				print('move z position to: ' + str(zPos)+ ' mm')

				xyzStage.goAbsolute('X', -xPos, False) #used to be -xPos - .035
				xyzStage.goAbsolute('Y', yPos, False)
				xyzStage.goAbsolute('Z', zPos, True)
 
				xyzStage.setVelocity('X',scanSpeed)
				xyzStage.setScanR(-xPos, -xPos + xLength)
				xyzStage.setScanV(yPos) 
	# 			# TURN GALVO ON
	# 			waveform = generator.waveformGenerator(100000, round(100000*nFrames*expTime/1000.0*1.15), 400, 1.4, 0)
	# 			waveform.start()

				#TURN LASER ON
				# if wavelengths.size > 1:
				# 	laser.setPower(wavelengths[i], initial_powers[i]*math.exp(j*zWidth/attenuations[i]))
				# 	laser.turnOn(wavelengths[i])
				# else:
				laser.setPower(initial_powers[i]) #power in mW
				laser.turnOn() #turn laser on

				# START SCAN
				hcam.startAcquisition() #start camera acquisition
				xyzStage.scan(False,laser) #modified LB 1-3-29 added ",laser"

				# CAPTURE IMAGES
				count_old = 0
				count_new = 0
				count = 0


				# FLAT FIELD CORRECTION		
				
				if flatField == 1:

					cal = tifffile.imread('C:\\Program Files\\cal.tif').astype(numpy.float32)
					cal = cal[int(1024-camY*binFactor/2):int(1024+camY*binFactor/2), :]
					cal = cal[0::binFactor, 0::binFactor]
					cal = cal/numpy.mean(cal[:])

					while count < nFrames-1:
						time.sleep(0.01)
						# Get frames.
						[frames, dims] = hcam.getFrames()
						count_old = count
						# Save frames.
						for aframe in frames:
							np_data = aframe.getData().astype(numpy.float32)
							im[count] = numpy.divide(numpy.clip(numpy.reshape(np_data, (camY, camX)) - bkg.astype(numpy.float32), 100*binFactor*binFactor, 65535) - 100*binFactor*binFactor, cal) #subtract background
							count += 1
						count_new = count
						if count_new == count_old:
							count = nFrames
						print(str(count_new) + '/' + str(nFrames) + ' frames collected...')
						data[count_old:count_new] = im[count_old:count_new]

				else: #if flat field correction = 0
					#after this loop, im.shape = (direction of X scan, direction of vertical FOV, direction of horizontal FOV) i.e. (X, Z, Y)
					while count < nFrames-1:
						time.sleep(0.01)
						# Get frames.
						[frames, dims] = hcam.getFrames()
						count_old = count
						# Save frames.
						for aframe in frames:
							np_data = aframe.getData()
							#im.append(numpy.reshape(np_data, (camY, camX)))
							im[count] = numpy.clip(numpy.reshape(np_data, (camY, camX)) - bkg, 100*binFactor*binFactor, 65535) - 100*binFactor*binFactor
							im[count] = numpy.reshape(np_data, (camY, camX)) #orient so camera's vertical FOV is row direction
							count += 1
						count_new = count
						if count_new == count_old:
							count = nFrames #reached last frame in scan
						print(str(count_new) + '/' + str(nFrames) + ' frames collected...')
						data[count_old:count_new] = im[count_old:count_new]
					

				#print('all' + str(nFrames) + 'frames collected')
				# TURN LASER OFF
				# if wavelengths.size > 1:
				# 	laser.turnOff(wavelengths[i])
				# else:
				laser.turnOff() #this is redundant but harmless as of 1-3-20, LB modified ms2000 to turn off laser

				#WRITE DOWNSAMPLED RESOLUTIONS
				print('im.shape = ' + str(im.shape))
				print('writing downsampled resolutions')
				if idx > 0: #
					previous_thread = write_threads[idx-1]
					while previous_thread.alive() == True:
						time.sleep(0.1)

				current_thread = utils.writeBDV(f, im, idx, binFactor)
				write_threads.append(current_thread)
				current_thread.start()

				if idx == (nWavelengths*yTiles*zTiles-1):
					current_thread.join()


				# WRITE VISUALIZATION FILE
				print('writing visualization file')
				print('im.shape = ' + str(im.shape))
				print('idx = ' + str(idx))

				hcam.stopAcquisition()
				gc.collect()

				
	# WRITES WHOLE FILE TO XML
	utils.write_xml(drive = drive, save_dir = save_dir, idx = idx, idx_tile = idx_tile, idx_channel = idx_channel, channels = nWavelengths, tiles_y = yTiles, tiles_z = zTiles, sampling = xWidth, binning = binFactor, offset_y = yStitchOverlay, offset_z = zStitchOverlay, x = imgShape[0], y = imgShape[1], z = imgShape[2])

	fWheel.shutDown()
	laser.shutDown()
	hcam.shutdown()
	f.close()

	xyzStage.setVelocity('X',0.5)
	xyzStage.setVelocity('Y',0.5)
	xyzStage.setVelocity('Z',0.5)			

	xyzStage.goAbsolute('X', initialPos[0], False)
	xyzStage.goAbsolute('Y', initialPos[1], False)
	xyzStage.goAbsolute('Z', initialPos[2], True)

	xyzStage.shutDown()
	
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
