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
import shutil
import logging
import tifffile

#this code will OVERWRITE the existing .xml file
sys.path.append('Z')
drive = 'Z'
save_dir = 'OTLS3_2020_imaging//UW_bladder//10-19-20_20X_OTLS3_Rob_UWbladder_15-049H' # specimen names
pxshiftYZ = 0 #number of pixels to shift 660nm relative to 488nm (if needed). (+) moves 660 UP and BACK relative to 488

#RUN "rewrite_utils" which rewrites the .xml file specified (in case stitching parameters need to be adjusted)
#must copy coordinates from the microscope run fil
xMin = -9.60#
xMax = -7.28 #4.98 #7.78 # #needs to be at least 2mm i think?
# ycenter = -14.11
yMin = -22.55 #ycenter - .385
yMax = -18.50#-18.72 #-7.31 #-2.73 #ycenter +.7
zMin = -2.37 # #zcenter - .01
zMax = -1.44 #-3.24 # #zcenter + .01 #if these numbers do not make sense, might get error "idx was referenced before assignment" #if these numbers do not make sense, might get error "idx was referenced before assignment"

#for ECi
#Dimensions of FOV
xWidth = 0.209 #in um, not mm (2nd gen system 0.48) 300um/1427px   --> 400um/1912px
yWidth = 0.385 # mm camera's horizontal FOV
zWidth = 0.03 #3 # mm calculated based on 610px/125um 11-20-19(2nd gen system 0.07)this will directly change how far z-strips are placed from each otehr in big stitcher
# LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
yStitchOverlay = 0.3825 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
zStitchOverlay = .03 #User-defined spacing between image tiles vertically, will affect XML file but not imaging
 
## For magnificaiton modificaitons
xWidth_ch1 = .206

# #for Ce3D 8-13-2020
# #1677 px = 1.5 mm = .8944 um/px lateral sampling. actual magnification = 7.26X
# xWidth = 0.894 #in um, not mm (2nd gen system 0.48) 
# yWidth = 1.75# 1.83 # mm camera's horizontal FOV
# zWidth = 0.14 #0.162 # mm calculated based on 610px/125um 11-20-19 
# # LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
# yStitchOverlay = yWidth #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
# zStitchOverlay = zWidth #User-defined spacing between image tiles vertically, will affect XML file but not imaging

# #for n = 1.46
# xWidth = 0.2212 #in um measure by moving stage in Y direction (300um stage movement per 1352 px) 1808px 400um
# yWidth = .45 #.453 #in mm camera's horizontal FOV
# zWidth = .0395#.0401 #in mm camera's vertical spacing, i.e. (um/px)*(256px)/sqrt(2)
# yStitchOverlay = .447 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
# zStitchOverlay = zWidth #User-defined spacing between image tiles vertically, will affect XML file but not imaging


binFactor = 1
camY = 256 # pixels
camX = 2048 # pixels
nWavelengths = 2
expTime = 10.0
######### PARAMETERS ###########
xMin = xMin - .05 #extra room for safety
xMax = xMax + .05
#y min = ymin-ywidth/2 and ymax = ymax + ywidth makes it so that it'll tile 1 tile to the left and right of your center
yMin = yMin #- yWidth/2 #to account for FOV/2 width not accounted for when estimating tissue bounds, + a little extra
yMax = yMax + yWidth/2

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
print('idx = ' + str(idx))

rewrite_utils.write_xml(drive = drive, save_dir = save_dir, idx = idx, idx_tile = idx_tile, idx_channel = idx_channel, channels = nWavelengths, tiles_y = yTiles, tiles_z = zTiles, sampling = xWidth, sampling_ch1 = xWidth_ch1, binning = binFactor, offset_y = yStitchOverlay, offset_z = zStitchOverlay, pxshiftYZ = pxshiftYZ, x = imgShape[0], y = imgShape[1], z = imgShape[2])
