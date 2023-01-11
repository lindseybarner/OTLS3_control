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
import generator.ni_LB as generator
import utils.utils_singleprocessing as utils_singleprocessing
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

	settings_dict = fc.getDefaultRGBSettings(use_default=True) #this stores settings for either nuclei or cyto
	nuclei_RGBsettings = settings_dict['nuclei']
	cyto_RGBsettings = settings_dict['cyto']
	nuc_normfactor = 4000
	cyto_normfactor = 30700


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
	yTiles = int(math.ceil(yLength/yWidth)) #int(round(yLength/yWidth)) #
	zTiles = int(round(zLength/zWidth))
	nTiles = zTiles*yTiles*len(wavelengths)
	nTiles_pcolor = yTiles*zTiles #number of tiles sans colors
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
		# userinput = input('this file directory already exists! permanently delete? [y/n]')
		# if userinput == 'y':
		shutil.rmtree(drive + ':\\' + save_dir, ignore_errors=True)
		# if userinput== 'n':
		# 	sys.exit('--Terminating-- re-name write directory and try again')

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
	
	############### SET UP GALVO ###############
	waveform = generator.waveformGenerator(freq = galvofreq, Xamplitude = galvoXamp, Xoffset = galvoXoffset, Yamplitude = 0, Yoffset = galvoYoffset[0])

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
	f_fc = h5py.File(dest_fc, 'a')

	idx_LB = 0
	fc_threads = 0
	for j in range(zTiles): 
		for k in range(yTiles): 
			for i in range(nWavelengths):

				# ############### SETUP LASERS ##############
				#Laser and filter wheel need to change every tile for imaging > 1 wavelength
				if wavelengths.size > 1:
					print('imaging >1 wavelengths')
					if wavelengths[i] == 660: ## added LB 1-6-20. i have separate lasers for different colors so this code is different than adam's
						waveform.adjust_Yoffset(galvoYoffset[i]) #adjusts focusing of light sheet (in and out of camera plane) per color
						fWheel.setPosition(660)
					if wavelengths[i] == 561:
						waveform.adjust_Yoffset(galvoYoffset[i])
						fWheel.setPosition(561)
					if wavelengths[i] == 488:
						waveform.adjust_Yoffset(galvoYoffset[i]) #adjusts focusing of light sheet (in and out of camera plane) per color
						fWheel.setPosition(488)

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
				data = f.require_dataset('/t00000/s' + str(idx).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, chunkSize2, chunkSize3), dtype = 'int16', shape = imgShape)#, compression = 32016, compression_opts=(round(2*1000), 1, round(2.1845*1000), 0, round(1.6*1000)))
			
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

				xyzStage.goAbsolute('X', -xPos, False) #used to be -xPos - .035
				xyzStage.goAbsolute('Y', yPos, False)
				xyzStage.goAbsolute('Z', zPos, True)
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
				im = numpy.zeros((nFrames, camY, camX), dtype = 'uint16') #initialize: "X" (scan) direction, Z (256px) direction, Y direction
				hcam.startAcquisition() #start camera acquisition
				if wavelengths[i] == 488:
					xyzStage.scan(False,laser488,-xPos) #laser turns off laser as soon as scan is done, and others commeand...
				if wavelengths[i] == 561:
					xyzStage.scan(False,laser561,-xPos) #laser turns off laser as soon as scan is done, and others commeand...
				if wavelengths[i] == 660:
					xyzStage.scan(False,laser660,-xPos) #laser turns off laser as soon as scan is done, and others commeand...

				# CAPTURE IMAGES
				count_old = 0
				count_new = 0
				count = 0

				while count < nFrames-1:
					time.sleep(0.01)
					# Get frames.
					print('getting frames')
					[frames, dims] = hcam.getFrames()
					count_old = count
					# Save frames.
					for aframe in frames:
						np_data = aframe.getData()
						im[count] = numpy.reshape(np_data, (256, 2048)) #orient so camera's vertical FOV is row direction
						count += 1
					count_new = count
					if count_new == count_old:
						print('reached last frame in scan')
						count = nFrames #reached last frame in scan
					print(str(count_new) + '/' + str(nFrames) + ' frames collected...')
					data[count_old:count_new] = im[count_old:count_new].astype('int16')

				if i == 0: ## cannot false color yet if only nuclear channel has been acquired
					data_ch0 = im

				if i == 1: #false color if on eosin channel
					t0 = time.time()
					data_ch1 = im
					idx_ch0 = int(idx + nTiles_pcolor*-1)

					## Create groups for each color
					for color in range(3):
						resgroup_fc = f_fc.create_group('/t00000/s' + str(idx_ch0 + nTiles_pcolor*color).zfill(2) + '/' + str(0))

					print('f_fc groups: ' + str(idx_ch0+nTiles_pcolor*0) + str(idx_ch0+nTiles_pcolor*1) + str(idx_ch0+nTiles_pcolor*2))
					## Initialize H5 formatting for each color
					data_fc_0 = f_fc.require_dataset('/t00000/s' + str(idx_ch0 + nTiles_pcolor*0).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, int(chunkSize2/4), chunkSize3), dtype = 'uint8', shape = imgShape_fc)
					data_fc_1 = f_fc.require_dataset('/t00000/s' + str(idx_ch0 + nTiles_pcolor*1).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, int(chunkSize2/4), chunkSize3), dtype = 'uint8', shape = imgShape_fc)
					data_fc_2 = f_fc.require_dataset('/t00000/s' + str(idx_ch0 + nTiles_pcolor*2).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, int(chunkSize2/4), chunkSize3), dtype = 'uint8', shape = imgShape_fc)
					
					im_3d = numpy.zeros((nFrames, int(camY/4), 2048, 3), dtype = 'uint8')
					z_fc = 0
					for z in range(0, camY, 4):
						im = fc.rapidFalseColor(data_ch0[:,z,:], data_ch1[:,z,:], nuclei_RGBsettings, cyto_RGBsettings, 
						        run_FlatField_cyto = False, run_FlatField_nuc = False, cyto_normfactor = cyto_normfactor, 
						        nuc_normfactor = nuc_normfactor, cyto_bg_threshold = 0, nuc_bg_threshold = 0, LBthresh = 'on')
						data_fc_0[:,z_fc,:] = im[:,:,0]
						data_fc_1[:,z_fc,:] = im[:,:,2]
						data_fc_2[:,z_fc,:] = im[:,:,1]
						im_3d[:,z_fc,:,:] = im
						z_fc += 1
					t1 = time.time()
					print('time taken to false color = ' + str(t1 - t0) + ' sec')

					#WRITE DOWNSAMPLED RESOLUTIONS
					# print('im.shape = ' + str(im.shape))
					print('writing downsampled resolutions')

					# utils_singleprocessing.writeBDV_fc(f_fc, im_3d[:,:,:,0], idx_ch0 + nTiles_pcolor*0, 1)
					# utils_singleprocessing.writeBDV_fc(f_fc, im_3d[:,:,:,2], idx_ch0 + nTiles_pcolor*1, 1)
					# utils_singleprocessing.writeBDV_fc(f_fc, im_3d[:,:,:,1], idx_ch0 + nTiles_pcolor*2, 1)
					# del im
					## fc_threads is a group of 3
					if fc_threads >= 1: ## If we have already a false-color session running
						previous_thread = write_threads[fc_threads*3 - 3:fc_threads*3]
						while previous_thread[-1].alive() == True:
							time.sleep(0.1)

					current_thread = utils.writeBDV_fc(f_fc, im_3d[:,:,:,0], idx_ch0 + nTiles_pcolor*0, 1)
					write_threads.append(current_thread)
					current_thread.start()
					
					current_thread = utils.writeBDV_fc(f_fc, im_3d[:,:,:,2], idx_ch0 + nTiles_pcolor*1, 1)
					write_threads.append(current_thread)
					current_thread.start()
					
					current_thread = utils.writeBDV_fc(f_fc, im_3d[:,:,:,1], idx_ch0 + nTiles_pcolor*2, 1)
					write_threads.append(current_thread)
					current_thread.start()

					fc_threads += 1

					if idx == (nWavelengths*yTiles*zTiles-1):
						current_thread.join()

				# 	previous_thread = write_threads[-2:] #previous_thread = write_threads[idx_LB-1]
				# 	while previous_thread[-2].alive() == True or previous_thread[-1].alive() == True:
				# 		time.sleep(0.1)

				# utils_singleprocessing.writeBDV(f, im, idx, binFactor)
				# current_thread1 = utils.writeBDV(f, im, idx, binFactor)
				# write_threads.append(current_thread1)
				# current_thread1.start()

				# if idx == (nWavelengths*yTiles*zTiles-1):
				# 	current_thread0.join()
				# 	current_thread1.join()
				# 	# current_thread2.join()

				hcam.stopAcquisition()
				gc.collect()
				idx_LB += 1
	print('idx = ' + str(idx))
	print('idx_ch0 + nTiles*color = ' + str(idx_ch0 + nTiles_pcolor*0))
	print('idx_ch0 + nTiles*color = ' + str(idx_ch0 + nTiles_pcolor*1))
	print('idx_ch0 + nTiles*color = ' + str(idx_ch0 + nTiles_pcolor*2))


	utils_singleprocessing.write_xml_fc(drive = drive, save_dir = save_dir, idx = idx_ch0 + nTiles*-1, idx_tile = idx_tile, idx_channel = 2, channels = 3, tiles_y = yTiles, tiles_z = zTiles, sampling = xWidth, binning = binFactor, binZ = 4, offset_y = yStitchOverlay, offset_z = zStitchOverlay, x = imgShape[0], y = imgShape[1], z = imgShape[2])
	print('idx_ch0 + nTiles*-1 = ' + str(idx_ch0 + nTiles*-1))		


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
