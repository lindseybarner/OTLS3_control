import ctypes
import ctypes.util
import numpy
import time
import math
import h5py
import warnings
import os
import os.path
import errno
import sys
import scipy.ndimage
import shutil
import warnings
import gc
import nidaqmx
import os
import os.path
from os import path

import camera.hamamatsu_camera as hc
import rs232.RS232 as RS232
import filter_wheel.fw102c_LB as fw102c_LB
import laser.obis as obis
import xyz_stage.ms2000 as ms2000
import utils.utils as utils
import lsmfx_LB as lsmfx_LB
import rewrite_utils

############# SCAN PARAMETERS #############
def lsm20X_batchrun_lindsey(drive, folder, x, y, z, expTime, wavelengths, laser_powers, galvoYoffset):

	sys.path.append(drive)
	base_dir = 'Users//User//Documents//'
	fname = base_dir + folder

	xMin = numpy.min(x)
	xMax = numpy.max(x)
	yMin = numpy.min(y)
	yMax = numpy.max(y)
	zMin = numpy.min(z)
	zMax = numpy.max(z)
	print('')

	#for ECi
	#Dimensions of FOV
	xWidth = 0.243 #in um, not mm (2nd gen system 0.48) 300um/1427px   --> 400um/1912px
	xWidth_ch1 = .243 #.207 #intended for BLUE
	yWidth = 0.499 # mm camera's horizontal FOV
	zWidth = 0.04 #3 # mm calculated based on 610px/125um 11-20-19(2nd gen system 0.07)this will directly change how far z-strips are placed from each otehr in big stitcher
	# LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
	yStitchOverlay = 0.385 #U ser-defined spacing between image tiles horizontally, will affect XML file but not imaging
	zStitchOverlay = .03 #User-d

	camY = 256 # pixels #"Z" direction, vertical in camera's FOV
	camX = 2048 # pixels "Y" direction, horizontal in camera's FOV
	camOffset = 0.0 # counts
	galvoXoffset = 3.03 #in V

	galvoXamp = 1.25 # in V. should be 1.5V for 20X imaging
	galvofreq = 1300 #in Hz. rule of thumb should tune to whatever minimum frequency looks "smooth" on the live camera feed
	binning = '2x2' #MUST change lsfmx to make compatible with pixel replacement
	flatField = 0

	######### PARAMETERS ###########
	xMin = xMin - .05
	# xMax = xMax + .10
	#y min = ymin-ywidth/2 and ymax = ymax + ywidth makes it so that it'll tile 1 tile to the left and right of your center
	yMin = yMin #- yWidth #to account for FOV/2 width not accounted for when estimating tissue bounds, + a little extra
	yMax = yMax + yWidth/2 

	######### INITIALIZE PARAMETERS ###########
	xLength = xMax - xMin # mm
	yLength = yMax - yMin #LB commented math.ceil((yMax - yMin)/yWidth)*yWidth # mm
	zLength = math.ceil((zMax - zMin)/zWidth)*zWidth # mm
	volume = xLength*yLength*zLength
	#Goal with yTiles is to cover whole area that user entered, + image extra if necessary
	yTiles = int(math.ceil(yLength/yWidth)) #consider adding 1 to this to fix error #previously int(round(yLength/yWidth))
	zTiles = int(round(zLength/zWidth))
	nTiles = zTiles*yTiles*len(wavelengths)
	# print('tissue volume = ' + str(volume) + 'mm^3')
	# print('number of tiles = ' + str(nTiles))
	print('folder name = ' + str(fname))
	xOff = xMax - (xLength)/2
	yOff = yMax - yLength/2
	zOff = zMin
	nFrames = int(round(xLength/(xWidth/1000))) #number of frames in X direction
	imgShape = (nFrames, camY, camX)
	###want to make sure that structure at center of coordinates will be imaged at center of FOV

	if binning == '1x1':
		binFactor = 1
	elif binning == '2x2':
		binFactor = 2
	elif binning == '4x4':
		binFactor = 4
	else:
		sys.exit('Bin factor invalid')

	print('zTiles = ' + str(zTiles))
	print('yTiles = ' + str(yTiles))
	for j in range(zTiles): 
		for k in range(yTiles):
			for i in range(len(wavelengths)):
				# print('j = ' +str(j))
				# print('k = ' + str(k))
				idx = k+j*yTiles+i*yTiles*zTiles
				idx_tile = k+j*yTiles
				idx_channel = i
				# print(idx)
				yPos = yOff- yLength/2.0 + k*yWidth #+ yWidth/2.0
				print('y = ' + str(yPos))
				zPos = j*zWidth + zOff
				# print('z = ' + str(zPos))
				# if zPos > -2.16:
				# 	print('j = ' + str(j))
				# 	print('z = ' + str(zPos))
	print('Max yPos = ' + str(yPos))
	print('Min zPos = ' + str(zPos))
	print('nFrames = ' + str(nFrames))
	scantime_singlestrip = xLength/(xWidth*binFactor/expTime)
	scantime_theoreticalmaxspeed = xLength/(xWidth*binFactor/1.25)
	time_reqd = (scantime_singlestrip+60)*nTiles/3600 #hrs
	current_time = time.time()
	completion_time = time.localtime(current_time + time_reqd*3600) #in seconds
	print('estimated time for imaging = ' + str(time_reqd) + 'hrs')
	print('estimated time at completion = ' + str(time.strftime("%a, %d %b %Y %I:%M:%S %p", completion_time)))
	# print('theoretical imaging time (max speed) = ' + str((scantime_theoreticalmaxspeed)*nTiles/60) + 'minutes')

	## Estimate memory required for this imaging job
	im = numpy.zeros((int(nFrames/binFactor),int(camY/binFactor),int(camX/binFactor)), dtype = 'int16')
	#Estimate memory required (generously). = memory of all tiles w 10X compression, 1 uncompressed tile in buffer, and multiply by 1.25 for margin
	mem_reqd =((im.size*im.itemsize)*nTiles/(1e9*10) + (im.size*im.itemsize)/(1e9))*1.25 #in GB, memory requirement estimated for this job (with 10X compression)
	mem_free = (shutil.disk_usage(drive + ':')[2])/1e9 #in GB
	del im

	if mem_free > mem_reqd:
		print('Disk space required = ' + str(mem_reqd) + ' GB')
		print('Disk space in drive = ' + str(mem_free) + ' GB')
		### BEGIN IMAGING ####
		lsmfx_LB.scan3D(drive, fname, xOff, yOff, zOff, xLength, yLength, zLength, xWidth, yWidth, zWidth, yStitchOverlay, zStitchOverlay, camY, camX, expTime, binning, wavelengths, laser_powers, galvoXoffset, galvoXamp, galvofreq, galvoYoffset, camOffset, flatField)
		# rewrite_utils.write_xml(drive = drive, save_dir = fname, idx = idx, idx_tile = idx_tile, idx_channel = idx_channel, channels = len(wavelengths), camX = camX, camY = camY, tiles_y = yTiles, tiles_z = zTiles, sampling = xWidth, sampling_ch1 = xWidth_ch1, binning = binFactor, offset_y = yStitchOverlay, offset_z = zStitchOverlay, pxshiftYZ = 0, x = imgShape[0], y = imgShape[1], z = imgShape[2])
	else:
		print('clear out drive before imaging!!')
		print('Disk space required = ' + str(mem_reqd) + ' GB')
		print('Disk space in drive = ' + str(mem_free) + ' GB')


	# time.sleep(30*60) ##Pause 30 minutes to let the camera cool down

