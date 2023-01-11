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


hcam = hc.HamamatsuCameraMR(camera_id=0)
print(hcam)


nFrames = 1000
camY = 256
camX = 2048
expTime = 20
binFactor = 1
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

hcam.setACQMode("fixed_length", nFrames)
hcam.startAcquisition() #start camera acquisition
count_old = 0
count_new = 0
count = 0
imgShape = (nFrames, camY, camX) 
chunkSize1 = 256/binFactor
chunkSize2 = 32/binFactor #for Z (256px) direction
chunkSize3 = 256/binFactor
idx = 0
im = numpy.zeros((nFrames, camY, camX), dtype = 'uint16') #initialize: "X" (scan) direction, Z (256px) direction, Y direction
dest = 'temp_data.h5'

if os.path.exists(dest):
	userinput = input('this file directory already exists! permanently delete? [y/n]')
	if userinput == 'y':
		shutil.rmtree(dest, ignore_errors=True)
	if userinput== 'n':
		sys.exit('--Terminating-- re-name write directory and try again')

f = h5py.File(dest,'a')
tgroup = f.create_group('/t00000')
resgroup = f.create_group('/t00000/s' + str(idx).zfill(2) + '/' + str(0))
data = f.require_dataset('/t00000/s' + str(0).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, chunkSize2, chunkSize3), dtype = 'int16', shape = imgShape, compression = 32016, compression_opts=(round(2*1000), 1, round(2.1845*1000), 0, round(1.6*1000)))
				
ts = time.gmtime()
print(time.strftime("%x %X", ts))
while count < nFrames-1:
	time.sleep(0.01)
	# Get frames.
	#print('getting frames')

	[frames, dims] = hcam.getFrames()
	count_old = count
	# Save frames.
	for aframe in frames:
		np_data = aframe.getData()
		#im.append(numpy.reshape(np_data, (camY, camX)))
		#im[count] = numpy.clip(numpy.reshape(np_data, (camY, camX)) - bkg, 100*binFactor*binFactor, 65535) - 100*binFactor*binFactor
		im[count] = numpy.reshape(np_data, (camY, camX)) #orient so camera's vertical FOV is row direction
		count += 1
	count_new = count
	if count_new == count_old:
		count = nFrames #reached last frame in scan
	#print(str(count_new) + '/' + str(nFrames) + ' frames collected...')
	data[count_old:count_new] = im[count_old:count_new]
hcam.stopAcquisition()
gc.collect()
hcam.shutdown()	
tnew = time.gmtime()
print(time.strftime("%x %X", tnew))
time_1000_frames = tnew-ts
