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
import lsmfx_LB_restart_crashed as lsmfx_LB_restart_crashed
import rewrite_utils


############# SCAN PARAMETERS #############
sys.path.append('E')
drive = 'E'
fname = '12-10-20_20X_OTLS3_GIC6004-3_2' # specimen names
copy_to_Zdrive = 'no'
xMin = 17.37 #
xMax = 26.19 #4.98 #7.78 # #needs to be at least 2mm i think?
# ycenter = -14.11
yMin = -11.17 #ycenter - .385
yMax = -8.16 #5.62 #4.30 #-18.72 #-7.31 #-2.73 #ycenter +.7
zMin = -2.58 # #zcenter - .01
zMax = -2.50 #-3.24 # #zcenter + .01 #if these numbers do not make sense, might get error "idx was referenced before assignment" #if these numbers do not make sense, might get error "idx was referenced before assignment"

#for ECi
#Dimensions of FOV
xWidth = 0.209 #in um, not mm (2nd gen system 0.48) 300um/1427px   --> 400um/1912px
xWidth_ch1 = .207 #intended for BLUE
yWidth = 0.385 # mm camera's horizontal FOV
zWidth = 0.03 #3 # mm calculated based on 610px/125um 11-20-19(2nd gen system 0.07)this will directly change how far z-strips are placed from each otehr in big stitcher
# LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
yStitchOverlay = 0.3825 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
zStitchOverlay = .03 #User-d

# #for n = 1.46
# xWidth = 0.2212 #in um measure by moving stage in Y direction (300um stage movement per 1352 px) 1808px 400um
# yWidth = .45 #.453 #in mm camera's horizontal FOV
# zWidth = .0395#.0401 #in mm camera's vertical spacing, i.e. (um/px)*(256px)/sqrt(2)
# yStitchOverlay = .447 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
# zStitchOverlay = zWidth #User-defined spacing between image tiles vertically, will affect XML file but not imagin

# #for Clearsee
# xWidth = 0.22779
# yWidth = .467
# zWidth = .04123
# yStitchOverlay = .46 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
# zStitchOverlay = .03 #User-defined spacing between image tiles vertically, will affect XML file but not imaging

camY = 256 # pixels #"Z" direction, vertical in camera's FOV
camX = 2048 # pixels "Y" direction, horizontal in camera's FOV
expTime = 30.0 #4.99 ms
camOffset = 0.0 # counts
wavelengths = numpy.array([660,488]) # lambda in nm
laser_powers = numpy.array([3,1]) #filter 1: 685+ filter 2: LP + single-band filter collects 495-552nm
galvoXoffset = 3.035 #in V
galvoYoffset = numpy.array([-.415, -.415]) #for 660nm, 488nm respectively. usually these numbers should be the same for 20X imaging

galvoXamp = 1.40 # in V. should be 1.5V for 20X imaging
galvofreq = 1000 #in Hz. rule of thumb should tune to whatever minimum frequency looks "smooth" on the live camera feed
binning = '1x1' #MUST change lsfmx to make compatible with pixel replacement
flatField = 0

######### PARAMETERS ###########
xMin = xMin - .05 #extra room for safety
xMax = xMax + .05
#y min = ymin-ywidth/2 and ymax = ymax + ywidth makes it so that it'll tile 1 tile to the left and right of your center
yMin = yMin #- yWidth/2 #to account for FOV/2 width not accounted for when estimating tissue bounds, + a little extra
yMax = yMax + yWidth#/2

######### INITIALIZE PARAMETERS ###########
xLength = xMax - xMin # mm
yLength = yMax - yMin #LB commented math.ceil((yMax - yMin)/yWidth)*yWidth # mm
zLength = math.ceil((zMax - zMin)/zWidth)*zWidth # mm
volume = xLength*yLength*zLength
#Goal with yTiles is to cover whole area that user entered, + image extra if necessary
yTiles = int(math.ceil(yLength/yWidth)) #consider adding 1 to this to fix error #previously int(round(yLength/yWidth))
zTiles = int(round(zLength/zWidth))
nTiles = zTiles*yTiles*len(wavelengths)
print('tissue volume = ' + str(volume) + 'mm^3')
print('number of tiles = ' + str(nTiles))
print('folder name = ' + str(fname))
xOff = xMax - (xLength)/2
yOff = yMax - yLength/2
zOff = zMin
nFrames = int(round(xLength/(xWidth/1000))) #number of frames in X direction
###want to make sure that structure at center of coordinates will be imaged at center of FOV

if binning == '1x1':
	binFactor = 1
elif binning == '2x2':
	binFactor = 2
elif binning == '4x4':
	binFactor = 4
else:
	binFactor = 1

if len(wavelengths) > 1: #check to make sure lasers are listed from red-->blue (just to keep convention consistent)
	if wavelengths[1] > wavelengths[0]:
		sys.exit('List wavelengths in decreasing order (lab convention for ch0 = 660nm')


# print('Y positions will be = ')
print('zTiles = ' + str(zTiles))
print('yTiles = ' + str(yTiles))
idx_LB = 0
for j in range(zTiles): 
	for k in range(yTiles):
		for i in range(len(wavelengths)):
			idx = k+j*yTiles+i*yTiles*zTiles
			if idx_LB == 30:
				print('Starting tile ' + str(idx_LB+1) + '/' + str(zTiles*yTiles*len(wavelengths))) #LB modified for indexing
				print('idx = ' + str(idx))
				print('j = ' + str(j))
				print('k = ' + str(k))
				print('i = ' + str(i))
			
			yPos = yOff- yLength/2.0 + k*yWidth #+ yWidth/2.0
			# print('y = ' + str(yPos))
			zPos = j*zWidth + zOff
			# print('z = ' + str(zPos))
			idx_LB += 1
print('Max yPos = ' + str(yPos))
print('Min zPos = ' + str(zPos))
print('nFrames = ' + str(nFrames))
scantime_singlestrip = xLength/(xWidth*binFactor/expTime)
scantime_theoreticalmaxspeed = xLength/(xWidth*binFactor/1.25)
print('estimated time for imaging = ' + str((scantime_singlestrip+60)*nTiles/3600) + 'hrs')
# print('theoretical imaging time (max speed) = ' + str((scantime_theoreticalmaxspeed)*nTiles/60) + 'minutes')

# ########### BEGIN SCANNING ##############
lsmfx_LB_restart_crashed.scan3D(drive, fname, xOff, yOff, zOff, xLength, yLength, zLength, xWidth, yWidth, zWidth, yStitchOverlay, zStitchOverlay, camY, camX, expTime, binning, wavelengths, laser_powers, galvoXoffset, galvoXamp, galvofreq, galvoYoffset, camOffset, flatField)
rewrite_utils.write_xml(drive = drive, save_dir = fname, idx = idx, idx_tile = idx_tile, idx_channel = idx_channel, channels = nWavelengths, camX = camX, camY = camY, tiles_y = yTiles, tiles_z = zTiles, sampling = xWidth, sampling_ch1 = xWidth_ch1, binning = binFactor, offset_y = yStitchOverlay, offset_z = zStitchOverlay, pxshiftYZ = pxshiftYZ, x = imgShape[0], y = imgShape[1], z = imgShape[2])
