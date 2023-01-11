#!/usr/bin/python


import numpy
import time
import math
import h5py
import warnings
import falsecolor as fc
import tifffile
import threading
import utils.utils_singleprocessing as utils_singleprocessing
import numpy as np
import ctypes
import ctypes.util
import numpy
import time
import math
import utils.utils_singleprocessing as utils_singleprocessing
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
from skimage import io

settings_dict = fc.getDefaultRGBSettings(use_default=True) #this stores settings for either nuclei or cyto
nuclei_RGBsettings = settings_dict['nuclei']
cyto_RGBsettings = settings_dict['cyto']
nuc_normfactor = 5500
cyto_normfactor = 60700


xMin = -7.37	#-1.81
xMax = -5.37 #needs to be at least 2mm i think?
#ycenter = -26.67
yMin = 5.58 ###ycenter - .385
yMax =  5.6 #ycenter +.7
zMin = -2.46 #zcenter - .01
zMax = -2.44 #-2.53 #-2.
xWidth = 0.8605 #measured with 561nm laser
xWidth_ch1 = 0.8605 #.8425 #for 488nm 
yWidth = 1.72 #1.76 #mm camera's horizontal FOV
zWidth = 0.12 #0.15 #0.151 # mm
# LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
yStitchOverlay = yWidth #1.72 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
zStitchOverlay = zWidth #User-defined spacing between image tiles vertically, will affect XML file but not imaging

camY = 256 # pixels #"Z" direction, vertical in camera's FOV
camX = 2048 # pixels "Y" direction, horizontal in camera's FOV
expTime = 7 
camOffset = 0.0 # counts
wavelengths = numpy.array([660, 488]) #H&E analog convention to list nuclear channel first
nWavelengths = len(wavelengths)

binFactor = 1
######### INITIALIZE PARAMETERS ###########
xMin = xMin - .05 #extra room for safety
xMax = xMax #+ .05
yMin = yMin #- yWidth/2#to account for FOV/2 width not accounted for when estimating tissue bounds, + a little extra
yMax = yMax + yWidth#/2

xLength = xMax - xMin # mm
yLength = yMax - yMin #LB commented math.ceil((yMax - yMin)/yWidth)*yWidth # mm
zLength = math.ceil((zMax - zMin)/zWidth)*zWidth # mm
volume = xLength*yLength*zLength
xOff = xMax - (xLength)/2
yOff = yMax - yLength/2
zOff = zMin
yTiles = int(round(yLength/yWidth)) #int(math.ceil(yLength/yWidth))  #
zTiles = int(round(zLength/zWidth))
xWidth = xWidth*binFactor
camY = int(camY/binFactor)
camX = int(camX/binFactor)
nFrames = int(round(xLength/(xWidth/1000))) #number of frames in X direction
yTiles = int(round(yLength/yWidth)) #int(math.ceil(yLength/yWidth))
zTiles = int(round(zLength/zWidth))
nTiles = yTiles*zTiles #number of tiles sans colorsimgShape = (nFrames, camY, camX)
imgShape = (nFrames, camY, camX) 
imgShape_fc = (nFrames, int(camY/4), camX)
chunkSize1 = 256/binFactor
chunkSize2 = 32/binFactor #for Z (256px) direction
chunkSize3 = 256/binFactor

if os.path.isfile('data_fc.h5'):
	os.remove('data_fc.h5')
dest_fc = 'data_fc.h5'
f_fc = h5py.File(dest_fc, 'a')

idx_LB = 0
for j in range(zTiles): 
	for k in range(yTiles):
		for i in range(len(wavelengths)):
			idx = k+j*yTiles+i*yTiles*zTiles
			idx_tile = k+j*yTiles
			idx_channel = i
			yPos = yOff- yLength/2.0 + k*yWidth #+ yWidth/2.0
			zPos = j*zWidth + zOff

			if idx == 0:
				tgroup = f_fc.create_group('/t00000')
				data_ch0 = io.imread('data_ch0.tiff')

			if idx == 1:
				data_ch1 = io.imread('data_ch1.tiff')
				idx_ch0 = int(idx + nTiles*-1)

				for color in range(3):
					resgroup_fc = f_fc.create_group('/t00000/s' + str(idx_ch0 + nTiles*color).zfill(2) + '/' + str(0))

				print('f_fc groups: ' + str(idx_ch0+nTiles*0) + str(idx_ch0+nTiles*1) + str(idx_ch0+nTiles*2))
				data_fc_0 = f_fc.require_dataset('/t00000/s' + str(idx_ch0 + nTiles*0).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, int(chunkSize2/4), chunkSize3), dtype = 'uint8', shape = imgShape_fc)
				data_fc_1 = f_fc.require_dataset('/t00000/s' + str(idx_ch0 + nTiles*1).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, int(chunkSize2/4), chunkSize3), dtype = 'uint8', shape =imgShape_fc)
				data_fc_2 = f_fc.require_dataset('/t00000/s' + str(idx_ch0 + nTiles*2).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, int(chunkSize2/4), chunkSize3), dtype = 'uint8', shape = imgShape_fc)
				
				im_3d = np.zeros((nFrames,int(camY/4),2048,3), dtype = 'uint8')
				z_fc = 0
				for z in range(0, camY, 4):
					im = fc.rapidFalseColor(data_ch0[:,z,:], data_ch1[:,z,:], nuclei_RGBsettings, cyto_RGBsettings, 
					        run_FlatField_cyto = False, run_FlatField_nuc = False, cyto_normfactor = cyto_normfactor, 
					        nuc_normfactor = nuc_normfactor, cyto_bg_threshold = 150, nuc_bg_threshold = 150, LBthresh = 'on')
					data_fc_0[:,z_fc,:] = im[:,:,0]
					data_fc_1[:,z_fc,:] = im[:,:,2]
					data_fc_2[:,z_fc,:] = im[:,:,1]
					im_3d[:,z_fc,:,:] = im
					z_fc += 1
			idx_LB += 1

utils_singleprocessing.writeBDV_fc(f_fc, im_3d[:,:,:,0], idx_ch0 + nTiles*0, 1)
utils_singleprocessing.writeBDV_fc(f_fc, im_3d[:,:,:,2], idx_ch0 + nTiles*1, 1)
utils_singleprocessing.writeBDV_fc(f_fc, im_3d[:,:,:,1], idx_ch0 + nTiles*2, 1)

drive = 'C'
save_dir = 'Users//User//Documents//OTLS3 Software and Installation//lsm-python'
utils_singleprocessing.write_xml_fc(drive = drive, save_dir = save_dir, idx = idx_ch0 + nTiles*-1, idx_tile = idx_tile, idx_channel = 2, channels = 3, tiles_y = yTiles, tiles_z = zTiles, sampling = xWidth, binning = binFactor, binZ = 4, offset_y = yStitchOverlay, offset_z = zStitchOverlay, x = imgShape[0], y = imgShape[1], z = imgShape[2])


f_fc.close()

		# data_fc = f_fc.require_dataset('/t00000/s' + str(idx_ch0 + .nTiles*0).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, int(chunkSize2/4), chunkSize3), dtype = 'uint8', shape = imgShape_fc)
		# data_fc = im_3d[:,:,:,0]
		# data_fc = f_fc.require_dataset('/t00000/s' + str(idx_ch0 + nTiles*1).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, int(chunkSize2/4), chunkSize3), dtype = 'uint8', shape =imgShape_fc)
		# data_fc = im_3d[:,:,:,2]
		# data_fc = f_fc.require_dataset('/t00000/s' + str(idx_ch0 + nTiles*2).zfill(2) + '/' + str(0) + '/cells', chunks = (chunkSize1, int(chunkSize2/4), chunkSize3), dtype = 'uint8', shape = imgShape_fc)
		# data_fc = im_3d[:,:,:,1]
		# 	im_3d[:,z_fc,:,:] = im
			



