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
import laser.sapphire as sapphire
import xyz_stage.ms2000 as ms2000
# import thorlabs_apt as apt
import generator.ni_LB as generator
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
import falsecolor as fc
import fc_h5
import threading

def scan3D(drive, save_dir, xoff, yoff, zoff, xLength, yLength, zLength, xWidth, yWidth, zWidth, yStitchOverlay, zStitchOverlay, camY, camX, expTime, binning, wavelengths, laser_powers,  galvoXoffset, galvoXamp, galvofreq, galvoYoffset, camOffset, flatField = 0, vis = 0):

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

	# ############## SETUP FALSECOLOR SETTINGS #################

	# settings_dict = fc.getDefaultRGBSettings(use_default=True) #this stores settings for either nuclei or cyto
	# nuclei_RGBsettings = settings_dict['nuclei']
	# cyto_RGBsettings = settings_dict['cyto']
	# nuc_normfactor = 5500
	# cyto_normfactor = 60700

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
	yTiles = int(math.ceil(yLength/yWidth))  #int(round(yLength/yWidth))
	zTiles = int(round(zLength/zWidth))
	nTiles = yTiles*zTiles #number of tiles sans colors
	scanSpeed = xWidth/expTime #um/ms or mm/sec # xWidth/(1.0/(1.0/(expTime/1000.0))*1000) LB modified to be simpler 11-22-19
	print('scanSpeed = ' + str(scanSpeed))

	print('number of frames in X direction = ' + str(nFrames))
	print('number of tiles in Y direction = ' + str(yTiles))
	print('number of tiles in Z direction = ' + str(zTiles))

	# Set aquisition mode
	hcam.setACQMode("fixed_length", nFrames)
		
	############# SETUP XYZ STAGE #############

	xyzStage = ms2000.MS2000(baudrate = 9600, port = 'COM6')
	xyzStage.setScanF(1)
	xyzStage.setBacklash(0)
	xyzStage.setTTL(0)
	initialPos = xyzStage.getPosition()
	print(xyzStage)


	############ SETUP FILTER WHEEL ###########

	fWheel = fw102c_LB.FW102C(baudrate = 115200, port = 'COM4')


	########## PREPARE FOR SCANNING ###########

	if os.path.exists(drive + ':\\' + save_dir):
		userinput = input('this file directory already exists! permanently delete? [y/n]')
		if userinput == 'y':
			shutil.rmtree(drive + ':\\' + save_dir, ignore_errors=True)
		if userinput== 'n':
			sys.exit('--Terminating-- re-name write directory and try again')

	time.sleep(1)
	os.makedirs(drive + ':\\' + save_dir)
	print(drive + ':\\' + save_dir)
	logging.basicConfig(filename=(drive + ':\\' + save_dir + '\\log.txt'))
	dest = drive + ':\\' + save_dir + '\\data.h5'
	dest_fc = drive + ':\\' + save_dir + '\\data_fc.h5'

	#save a copy of executed python files to drive for record
	shutil.copyfile('lsm5X_LB_run.py', drive + ':\\' + save_dir + '\\lsm5X_LB_run.py')
	shutil.copyfile('lsm20X_LB_run.py', drive + ':\\' + save_dir + '\\lsm20X_LB_run.py')
	shutil.copyfile('lsmfx_LB.py', drive + ':\\' + save_dir + '\\lsmfx_LB.py')
	shutil.copyfile('filter_wheel\\fw102c_LB.py', drive + ':\\' + save_dir + '\\fw102c_LB.py')

	imgShape = (nFrames, camY, camX) 
	imgShape_fc = (nFrames, int(camY/4), camX)
	chunkSize1 = 256/binFactor
	chunkSize2 = 32/binFactor #for Z (256px) direction
	chunkSize3 = 256/binFactor
	write_threads = []
	im = numpy.zeros((nFrames, camY, camX), dtype = 'uint16') #initialize: "X" (scan) direction, Z (256px) direction, Y direction


	############### SET UP GALVO ###############
	waveform = generator.waveformGenerator(freq = galvofreq, Xamplitude = galvoXamp, Xoffset = galvoXoffset, Yamplitude = 0, Yoffset = galvoYoffset[0])

	#Set up lasers. do this before the loop because 561 laser has trouble initializing
	#if nWavelengths = 1, galvo laser and fWheel will be set (no need for changes within loop)
	for i in range(nWavelengths):
		if wavelengths[i] == 660:
			laser660 = obis.Obis(baudrate = 9600, port = 'COM5') ## Used to be COM9, temporarily COM5 and 561 is unplugged
			fWheel.setPosition(660)
			waveform.adjust_Yoffset(galvoYoffset[i])
		if wavelengths[i] == 561:
			laser561 = sapphire.SapphireLaser(com = 'COM13')	
			fWheel.setPosition(561)
			waveform.adjust_Yoffset(galvoYoffset[i])
		if wavelengths[i] == 488:
			laser488 = obis.Obis(baudrate = 9600, port = 'COM3')
			fWheel.setPosition(488)	
			waveform.adjust_Yoffset(galvoYoffset[i])

	############## START SCANNING ############
	
	f = h5py.File(dest,'a')
	f_fc = h5py.File(dest_fc,'a')
	idx_LB = 0

	for j in range(zTiles): 
		for k in range(yTiles): 
			for i in range(nWavelengths):

				# ############### SETUP LASERS ##############
				#Laser and filter wheel need to change every tile for imaging > 1 wavelength
				if wavelengths.size > 1:
					print('imaging >1 wavelengths')
					if wavelengths[i] == 660: ## added LB 1-6-20. i have separate lasers for different colors so this code is different than adam's
						#refer to laser660
						waveform.adjust_Yoffset(galvoYoffset[i]) #adjusts focusing of light sheet (in and out of camera plane) per color
						fWheel.setPosition(660)
					if wavelengths[i] == 561:
						#refer to laser561
						waveform.adjust_Yoffset(galvoYoffset[i])
						fWheel.setPosition(561)
					if wavelengths[i] == 488:
						#refer to laser488
						waveform.adjust_Yoffset(galvoYoffset[i]) #adjusts focusing of light sheet (in and out of camera plane) per color
						fWheel.setPosition(488)
						#userinput = input('change Y galvo offset to -0.65V before proceeding to 488nm. hit enter when done')

				# if wavelengths.size > 1:
				# 	fWheel.setPosition(wavelengths[i])
				# else:
				# 	fWheel.setPosition(wavelengths[i])

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
					tgroup_fc = f_fc.create_group('/t00000')
				resgroup = f.create_group('/t00000/s' + str(idx).zfill(2) + '/' + str(0))
				resgroup_fc = f_fc.create_group('/t00000/s' + str(idx).zfill(2) + '/' + str(0))
				data = f.require_dataset('/t00000/s' + str(idx).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, chunkSize2, chunkSize3), dtype = 'int16', shape = imgShape, compression = 32016, compression_opts=(round(2*1000), 1, round(2.1845*1000), 0, round(1.6*1000)))
			
				# GO TO INITIAL POSITIONS
				moveSpeed = .5
				xyzStage.setVelocity('X',moveSpeed) #used to be .5
				xyzStage.setVelocity('Y',moveSpeed) #used to be .5
				xyzStage.setVelocity('Z',moveSpeed) #used to be .5

				xPos = xLength/2.0 - xoff
				yPos = -yLength/2.0+k*yWidth + yoff 
				zPos = j*zWidth + zoff
				print('Starting tile ' + str(idx_LB+1) + '/' + str(zTiles*yTiles*nWavelengths)) #LB modified for indexing
				ts = time.gmtime()
				print(time.strftime("%x %X", ts))
				print('move x position to: ' + str(-xPos)+ ' mm') #modified LB 11-17-19, used to be str(-xPos-.035)
				print('move y position to: ' + str(yPos)+ ' mm')
				print('move z position to: ' + str(zPos)+ ' mm')

				xyzStage.goAbsolute('X', -xPos, False) #used to be -xPos - .035
				xyzStage.goAbsolute('Y', yPos, False)
				xyzStage.goAbsolute('Z', zPos, True)

				if scanSpeed > 0.5:
					raise Exception('Scan speed has been set to > 0.5mm/s! This could cause sample movement')

				xyzStage.setVelocity('X',scanSpeed)
				xyzStage.setScanR(-xPos, -xPos + xLength)
				xyzStage.setScanV(yPos) 

				if wavelengths[i] == 488:
					laser488.setPower(laser_powers[i]) #power in mW
					laser488.turnOn() #turn laser on
				if wavelengths[i] == 561:
					laser561.setPower(laser_powers[i]) #power in mW
					laser561.turnOn() #turn laser on
				if wavelengths[i] == 660:
					laser660.setPower(laser_powers[i]) #power in mW
					laser660.turnOn() #turn laser on 


				# START SCAN
				hcam.startAcquisition() #start camera acquisition
				if wavelengths[i] == 488:
					xyzStage.scan(False,laser488,-xPos) #laser turns off laser as soon as scan is done, and others commeand...
				if wavelengths[i] == 561:
					xyzStage.scan(False,laser561,-xPos) #laser turns off laser as soon as scan is done, and others commeand...
				if wavelengths[i] == 660:
					xyzStage.scan(False,laser660,-xPos) #laser turns off laser as soon as scan is done, and others commeand...
				
				#stage to go back to original position as soon as scan is done at scanSpeed. modified LB 1-3-29 and 2-3-20

				# CAPTURE IMAGES
				count_old = 0
				count_new = 0
				count = 0

				#after this loop, im.shape = (direction of X scan, direction of vertical FOV, direction of horizontal FOV) i.e. (X, Z, Y)
				while count < nFrames-1:
					time.sleep(0.01)
					# Get frames.
					print('getting frames')
					[frames, dims] = hcam.getFrames()
					count_old = count
					# Save frames.
					for aframe in frames:
						np_data = aframe.getData()
						im[count] = numpy.reshape(np_data, (camY, camX)) #orient so camera's vertical FOV is row direction
						count += 1
					count_new = count
					if count_new == count_old:
						count = nFrames #reached last frame in scan
					print(str(count_new) + '/' + str(nFrames) + ' frames collected...')
					im[:,248,1922] = im[:,248,1920] #x = 1921, y = 248 is a dead pixel on camera
					im[:,248,1921] = im[:,247,1921] #x = 1923, y = 248 is also faulty but not as bad
					im[:,248,1923] = im[:,249,1923]
					data[count_old:count_new] = im[count_old:count_new].astype('int16')

				if i == 0:
					data_ch0 = data.copy()

				if i == 1: #false color if on eosin channel
					# Set up h5 file for each color
					data_fc_0 = f_fc.require_dataset('/t00000/s' + str(idx + nTiles*0).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, int(chunkSize2/4), chunkSize3), dtype = 'uint8', shape = imgShape_fc)
					data_fc_1 = f_fc.require_dataset('/t00000/s' + str(idx + nTiles*1).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, int(chunkSize2/4), chunkSize3), dtype = 'uint8', shape = imgShape_fc)
					data_fc_2 = f_fc.require_dataset('/t00000/s' + str(idx + nTiles*2).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, int(chunkSize2/4), chunkSize3), dtype = 'uint8', shape = imgShape_fc)
					
					# Write falsecolored data to h5 file
					current_thread0 = fc_h5.fc_h5(data_ch0, data, data_fc_0, data_fc_1, data_fc_2, idx, camY, 4)
					write_threads.append(current_thread0)
					current_thread0.start()

				#WRITE DOWNSAMPLED RESOLUTIONS
				print('im.shape = ' + str(im.shape))
				print('writing downsampled resolutions')
				if idx_LB > 0: #
					previous_thread = write_threads[-2:] #previous_thread = write_threads[idx_LB-1]
					while previous_thread[-2].alive() == True or previous_thread[-1].alive() == True:
						time.sleep(0.1)

				current_thread1 = utils.writeBDV(f, im, idx, binFactor)
				write_threads.append(current_thread1)
				current_thread1.start()

				### Write downsampled resolutions for falsecolored file
				for color in range(3):
					util.writeBDV_fc(f_fc, im, idx + nTiles*color, binFactor)
				# current_thread2 = utils.writeBDV_fc(f_fc, im, idx, binFactor)
				# write_threads.append(current_thread2)
				# current_thread2.start()

				if idx == (nWavelengths*yTiles*zTiles-1):
					current_thread0.join()
					current_thread1.join()
					# current_thread2.join()


				# WRITE VISUALIZATION FILE
				print('writing visualization file')
				print('im.shape = ' + str(im.shape))
				print('idx = ' + str(idx))

				hcam.stopAcquisition()
				gc.collect()
				idx_LB += 1
	print('idx = ' + str(idx))
	print('idx_tile = ' + str(idx_tile))
	print('idx_channel = ' + str(idx_channel))
	print('channels = ' + str(nWavelengths))
				
	# WRITES WHOLE FILE TO XML
	utils.write_xml(drive = drive, save_dir = save_dir, idx = idx, idx_tile = idx_tile, idx_channel = idx_channel, channels = nWavelengths, tiles_y = yTiles, tiles_z = zTiles, sampling = xWidth, binning = binFactor, offset_y = yStitchOverlay, offset_z = zStitchOverlay, x = imgShape[0], y = imgShape[1], z = imgShape[2])

	fWheel.shutDown()
	waveform.stop() #stops galvo
	hcam.shutdown()
	f.close()
	f_fc.close()

	#Shut down all lasers
	for i in range(nWavelengths):
		if wavelengths[i] == 660:
			laser660.shutDown()
		if wavelengths[i] == 561:
			laser561.shutDown()
		if wavelengths[i] == 488:
			laser488.shutDown()

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
