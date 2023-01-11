import ctypes
import ctypes.util
import numpy
import time
import math
# import thorlabs_apt as apt
# import generator.ni as generator
# import utils.findbounds as findbounds
import utils.utils as utils
import rewrite_utils
import rewrite_utils_unshear_data
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

#this code will OVERWRITE the existing .xml file
sys.path.append('X')
drive = 'X'
save_dir = '3-4-20_20X_OTLS3_33E_TILS//unshear_data_test' # specimen names

#RUN "rewrite_utils" which rewrites the .xml file specified (in case stitching parameters need to be adjusted)
#must copy coordinates from the microscope run fil

xMin = 6.5
xMax = 7.5 #needs to be at least 2mm i think?
ycenter = -26.67
yMin = ycenter - .385
yMax = ycenter +.7
#zcenter = -2.1
zMin = -2.5 #zcenter - .01
zMax = -1.9 #zcenter + .01 #if these numbers do not make sense, might get error "idx was referenced before assignment" #if these numbers do not make sense, might get error "idx was referenced before assignment"

#for ECi
#Dimensions of FOV
xWidth = 0.20 #in um, not mm (2nd gen system 0.48) 
yWidth = 0.385 # mm camera's horizontal FOV
zWidth = 0.03 #3 # mm calculated based on 610px/125um 11-20-19(2nd gen system 0.07)this will directly change how far z-strips are placed from each otehr in big stitcher
# LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
yStitchOverlay = 0.3675 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
zStitchOverlay = .0255 #User-defined spacing between image tiles vertically, will affect XML file but not imaging

# #for Clearsee
# xWidth = 0.22779
# yWidth = .467
# zWidth = .04123
# yStitchOverlay = .46 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
# zStitchOverlay = .03 #User-defined spacing between image tiles vertically, will affect XML file but not imaging

xMin = xMin - .05 #extra room for safety
xMax = xMax + .05
yMin = yMin #- yWidth/2#to account for FOV/2 width not accounted for when estimating tissue bounds, + a little extra
yMax = yMax #+ yWidth/2


binFactor = 1
camY = 256 # pixels
camX = 2048 # pixels
nWavelengths = 2
expTime = 20 # ms
xLength = xMax - xMin # mm
yLength = yMax - yMin #LB commented math.ceil((yMax - yMin)/yWidth)*yWidth # mm
zLength = math.ceil((zMax - zMin)/zWidth)*zWidth # mm
xOff = xMax - (xLength)/2
yOff = yMax - yLength/2
zOff = zMin

xWidth = xWidth*binFactor
camY = int(camY/binFactor)
camX = int(camX/binFactor)
nFrames = int(round(xLength/(xWidth/1000))) #number of frames in X direction
yTiles = int(round(yLength/yWidth))
zTiles = int(round(zLength/zWidth))
imgShape = (nFrames, camY, camX)

im = numpy.zeros((nFrames, camY, camX), dtype = 'uint16') #initialize: "X" (scan) direction, Z (256px) direction, Y direction

i = 1
vis = 0

Ntiles = zTiles*yTiles*nWavelengths
for j in range(zTiles): 
	for k in range(yTiles): 
		for i in range(nWavelengths):
			idx = k+j*yTiles+i*yTiles*zTiles
			idx_tile = k+j*yTiles
			idx_channel = i

							# GET NAME FOR NEW VISUALIZATION FILE
			if idx == 0:
				dest_vis = drive + ':\\' + save_dir + '\\vis' + str(idx) + '.h5'
			else:
				dest_vis = drive + ':\\' + save_dir + '\\vis' + str(idx) + '.h5'
				dest_vis_prev = drive + ':\\' + save_dir + '\\vis' + str(idx-1) + '.h5'

			# WRITE VISUALIZATION FILE
			#print('writing visualization file')
			#print('im.shape = ' + str(im.shape))
print('idx = ' + str(idx))

rewrite_utils_unshear_data.write_xml(drive = drive, save_dir = save_dir, idx = idx, idx_tile = idx_tile, idx_channel = idx_channel, channels = nWavelengths, tiles_y = yTiles, tiles_z = zTiles, sampling = xWidth, binning = binFactor, offset_y = yStitchOverlay, offset_z = zStitchOverlay, x = imgShape[0], y = imgShape[1], z = imgShape[2])
