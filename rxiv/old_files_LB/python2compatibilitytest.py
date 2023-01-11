#!python2
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
# import laser.skyra as skyra
import xyz_stage.ms2000 as ms2000
# import thorlabs_apt as apt
# import generator.ni as generator
# import utils.findbounds as findbounds
import utils.utils as utils
# import utils.background as background
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

def py2test(drive, save_dir, xoff, yoff, zoff, xLength, yLength, zLength, xWidth, yWidth, zWidth, camY, camX, expTime, binning, wavelengths, initial_powers, motor_positions, attenuations, camOffset, flatField = 0, vis = 0):

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

	# bkg = background.backgroundSubtract(camX, camY, expTime, binning) - 100*binFactor*binFactor

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
	#nFrames = int(round(xLength/(xWidth/1000))) #number of frames in X direction
	nFrames = 2048 #this is a test, trying to solve chunking/data size error in visualization 11.16.19
	yTiles = int(round(yLength/yWidth))
	zTiles = int(round(zLength/zWidth))
	scanSpeed = xWidth/(1.0/(1.0/(expTime/1000.0))*1000)

	print('number of frames in X direction = ' + str(nFrames))
	print('number of tiles in Y direction = ' + str(yTiles))
	print('number of tiles in Z direction = ' + str(zTiles))

	# Set aquisition mode
	hcam.setACQMode("fixed_length", nFrames)
		
	############# SETUP XYZ STAGE #############

	xyzStage = ms2000.MS2000(baudrate = 9600, port = 'COM1')
	xyzStage.setScanF(1)
	xyzStage.setBacklash(0)
	xyzStage.setTTL(0)
	initialPos = xyzStage.getPosition()
	print(xyzStage)

	fWheel = fw102c_LB.FW102C(baudrate = 115200, port = 'COM4')
	fWheel.shutDown()
	# laser.shutDown()
	hcam.shutdown()
	f.close()


	xyzStage.shutDown()