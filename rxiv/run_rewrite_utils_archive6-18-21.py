import ctypes
import ctypes.util
import numpy
import time
import math
import utils.utils as utils
import rewrite_utils
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
import shutil # mm camera's horizontal FOV
import logging
import tifffile

#this code will OVERWRITE the existing .xml file
sys.path.append('Z')
drive = 'Z'
save_dir = 'Lindsey/OTLS3_2021_imaging//breast_cancer_LN' # specimen names
pxshiftYZ = 0 #number of pixels to shift 660nm relative to 488nm (if needed). (+) moves 660 UP and BACK relative to 488

#RUN "rewrite_utils" which rewrites the .xml file specified (in case stitching parameters need to be adjusted)
#must copy coordinates from the microscope run fil
xMin = 1.43
xMax = 13.5 #19.02 #needs to be at least 2mm i think?
#ycenter = -26.67
yMin = -6.54 #-19.65 #ycenter - .385
yMax = 2.49 #-18.29 #ycenter +.7
zMin = -3.17 #-2.75 #zcenter - .01
zMax = -1.13 #-2.54 #zcenter + .01 #if these numbers do not make sense, might get error "idx was referenced before assignment" #if these numbers do not make sense, might get error "idx was referenced before assignment"

# for ECi
xWidth = 0.209 #in um, not mm (2nd gen system 0.48) 300um/1427px   --> 400um/1912px
xWidth_ch1 = .207 #intended for BLUE
yWidth = 0.385 # mm camera's horizontal FOV
zWidth = 0.03 #3 # mm calculated based on 610px/125um 11-20-19(2nd gen system 0.07)this will directly change how far z-strips are placed from each otehr in big stitcher
# LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
yStitchOverlay = 0.38 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
zStitchOverlay = .03 #User-d

# for CUBIC n = 1.518
xWidth = 0.8605 #measured with 561nm laser
xWidth_ch1 = 0.8605 #.8425 #for 488nm 
yWidth = 1.72 #1.76 #mm camera's horizontal FOV
zWidth = 0.12 #0.15 #0.151 # mm
# LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
yStitchOverlay = yWidth #1.72 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
zStitchOverlay = zWidth #User-defined spacing between image tiles vertically, will affect XML file but not imaging



binFactor = 1
camY = 256 # pixels
camX = 2048 # pixels
nWavelengths = 2
expTime = 10.0
######### PARAMETERS ###########
xMin = xMin - .05 #extra room for safety
xMax = xMax #+ .05
#y min = ymin-ywidth/2 and ymax = ymax + ywidth makes it so that it'll tile 1 tile to the left and right of your center
yMin = yMin #- yWidth/2 #to account for FOV/2 width not accounted for when estimating tissue bounds, + a little extra
yMax = yMax + yWidth #/2

######### INITIALIZE PARAMETERS ###########
xLength = xMax - xMin # mm
yLength = yMax - yMin #LB commented math.ceil((yMax - yMin)/yWidth)*yWidth # mm
zLength = math.ceil((zMax - zMin)/zWidth)*zWidth # mm
volume = xLength*yLength*zLength
yTiles = int(math.ceil(yLength/yWidth))# int(round(yLength/yWidth)) #LB "math.ceil" used to be "round"
zTiles = int(round(zLength/zWidth))
nTiles = zTiles*yTiles*nWavelengths

xOff = xMax - (xLength)/2
yOff = yMax - yLength/2
zOff = zMin
nFrames = int(round(xLength/(xWidth/1000))) #number of frames in X directionactor
camY = int(camY/binFactor)
camX = int(camX/binFactor)
nFrames = int(round(xLength/(xWidth/1000))) #number of frames in X direction
yTiles = int(math.ceil(yLength/yWidth))#int(round(yLength/yWidth))
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
# print('idx = ' + str(idx))

rewrite_utils.write_xml(drive = drive, save_dir = save_dir, idx = idx, idx_tile = idx_tile, idx_channel = idx_channel, channels = nWavelengths, camX = camX, camY = camY, tiles_y = yTiles, tiles_z = zTiles, sampling = xWidth, sampling_ch1 = xWidth_ch1, binning = binFactor, offset_y = yStitchOverlay, offset_z = zStitchOverlay, pxshiftYZ = pxshiftYZ, x = imgShape[0], y = imgShape[1], z = imgShape[2])
