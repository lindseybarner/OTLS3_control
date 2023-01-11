import ctypes
import ctypes.util
import numpy
import time
import math
# import thorlabs_apt as apt
# import generator.ni as generator
# import utils.findbounds as findbounds
import utils.utils as utils
import rewrite_utils_5Xcolorshift
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
drive = 'Z'
save_dir = 'OTLS3_Spring2020_imaging\\Stevens_lab\\8_12_20_5X_OTLS3_StevensCe3D_528' # specimen names
pxshiftYZ = 5 #number of pixels to shift one color relative to the other
pxshiftX = 0 #4 #shift tiles on top backwards relative to tiles below, if any stage tilt

#RUN "rewrite_utils" which rewrites the .xml file specified (in case stitching parameters need to be adjusted)
#must copy coordinates from the microscope run file
xMin = 25.25 #17.36
xMax = 32.55 #needs to be at least 2mm i think?
#ycenter = -26.67
yMin = -10.82 #-19.65 #ycenter - .385
yMax = -4.0 #-6.17 #ycenter +.7
zMin = -3.65 #zcenter - .01
zMax = -3.45 #zcenter + .01 #if these numbers do not make sense, might get error "idx was referenced before assignment" #if these numbers do not make sense, might get error "idx was referenced before assignment"

# # for ECi
# xWidth = 0.834 #in um, not mm (2nd gen system 0.48) 
# yWidth = 1.65# 1.708 # mm camera's horizontal FOV
# zWidth = 0.12 #0.151 # mm calculated based on 610px/125um 11-20-19 
# # LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
# yStitchOverlay = 1.635 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
# zStitchOverlay = zWidth #User-defined spacing between image tiles vertically, will affect XML file but not imaging

#for Ce3D 8-13-2020
#1677 px = 1.5 mm = .8944 um/px lateral sampling. actual magnification = 7.26X
xWidth = 0.894 #in um, not mm (2nd gen system 0.48) 
yWidth = 1.75# 1.83 # mm camera's horizontal FOV
zWidth = 0.14 #0.162 # mm calculated based on 610px/125um 11-20-19 
# LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
yStitchOverlay = yWidth #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
zStitchOverlay = zWidth #User-defined spacing between image tiles vertically, will affect XML file but not imaging


binFactor = 1
camY = 256 # pixels
camX = 2048 # pixels
expTime = 25 # ms
xMin = xMin - .05 #extra room for safety
xMax = xMax + .05
yMin = yMin #- yWidth/2#to account for FOV/2 width not accounted for when estimating tissue bounds, + a little extra
yMax = yMax #+ yWidth/2

xLength = xMax - xMin # mm
yLength = yMax - yMin # mm
zLength = math.ceil((zMax - zMin)/zWidth)*zWidth # mm
xOff = xMax - (xLength)/2
yOff = yMax - yLength/2
zOff = zMin

xWidth = xWidth*binFactor
camY = int(camY/binFactor)
camX = int(camX/binFactor)
nFrames = int(round(xLength/(xWidth/1000))) #number of frames in X direction
yTiles = int(math.ceil(yLength/yWidth))  #int(round(yLength/yWidth))
zTiles = int(round(zLength/zWidth))
imgShape = (nFrames, camY, camX)

im = numpy.zeros((nFrames, camY, camX), dtype = 'uint16') #initialize: "X" (scan) direction, Z (256px) direction, Y direction

i = 1
vis = 0
nWavelengths = 3
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

print('xOff' + str(xOff))
print('yOff' + str(yOff))
print('xLength' + str(xLength))
print('yLength' + str(yLength))

rewrite_utils_5Xcolorshift.write_xml(drive = drive, save_dir = save_dir, idx = idx, idx_tile = idx_tile, idx_channel = idx_channel, channels = nWavelengths, tiles_y = yTiles, tiles_z = zTiles, sampling = xWidth, binning = binFactor, offset_y = yStitchOverlay, offset_z = zStitchOverlay, pxshiftYZ = pxshiftYZ, pxshiftX = pxshiftX, x = imgShape[0], y = imgShape[1], z = imgShape[2])