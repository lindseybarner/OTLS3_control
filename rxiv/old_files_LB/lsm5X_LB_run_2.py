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
import shutil

# import camera.hamamatsu_camera as hc
# import rs232.RS232 as RS232
# import filter_wheel.fw102c_LB as fw102c_LB
# import laser.obis as obis
# import xyz_stage.ms2000 as ms2000
# import utils.utils as utils
# import lsmfx_LB


############# NEW SAMPLE #############
sys.path.append('E')
drive = 'E'
fname = '10_27_20_5X_OTLS3_liver_13_2' # specimen names
copy_to_Zdrive = 'no'
xMin = 14.39 #17.36
xMax = 23.71 #19.02 #needs to be at least 2mm i think?
#ycenter = -26.67
yMin = -22.39 #-19.65 #ycenter - .385
yMax = -18.21 #-12.33 #ycenter +.7
zMin = -2.71 #-2.75 #zcenter - .01
zMax = -2.20 #-2.

# for ECi
xWidth = 0.834 #in um, not mm (2nd gen system 0.48) 
yWidth = 1.65# 1.708 # mm camera's horizontal FOV
zWidth = 0.12 #0.151 # mm calculated based on 610px/125um 11-20-19 
# LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
yStitchOverlay = 1.6275 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
zStitchOverlay = zWidth #User-defined spacing between image tiles vertically, will affect XML file but not imaging

# #for n = 1.46 8-13-2020
# #1677 px = 1.5 mm = .8944 um/px lateral sampling. actual magnification = 7.26X
# xWidth = 0.894 #in um, not mm (2nd gen system 0.48) 
# yWidth = 1.75# 1.83 # mm camera's horizontal FOV
# zWidth = 0.14 #0.162 # mm calculated based on 610px/125um 11-20-19 
# # LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
# yStitchOverlay = yWidth #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
# zStitchOverlay = zWidth #User-defined spacing between image tiles vertically, will affect XML file but not imaging



# # for n = 1.41 ClearSee 2-8-2020
# xWidth = 0.904 #in um, not mm (2nd gen system 0.48) 
# yWidth = 1.85# 1.708 # mm camera's horizontal FOV
# zWidth = .15 #0.1637 # # mm 
# # LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
# yStitchOverlay = 1.85 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
# zStitchOverlay = .14 #User-defined spacing between image tiles vertically, will affect XML file but not imaging

camY = 256 # pixels #"Z" direction, vertical in camera's FOV
camX = 2048 # pixels "Y" direction, horizontal in camera's FOV
expTime = 25 #4.99 ms
camOffset = 0.0 # counts
wavelengths = numpy.array([660,488]) # SWITCHED 488 FILTER SETTING SO THAT IT DOES FILTER 4 9-11-20
laser_powers = numpy.array([2,3])
galvoXoffset = 2.38
galvoYoffset = numpy.array([-.08,.05]) #for 660nm, 488nm respectively. usually these numbers are not the same for 5X imaging.
galvoXamp = 6.1 # in V. should be 1.5V for 20X imaging
galvofreq = 1000 #in Hz. rule of thumb should tune to whatever minimum frequency looks "smooth" on the live camera feed
binning = '1x1'#'1x1'
flatField = 0
######### INITIALIZE PARAMETERS ###########
xMin = xMin - .05 #extra room for safety
xMax = xMax + .05
yMin = yMin #- yWidth/2#to account for FOV/2 width not accounted for when estimating tissue bounds, + a little extra
yMax = yMax + yWidth/2


xLength = xMax - xMin # mm
yLength = yMax - yMin #LB commented math.ceil((yMax - yMin)/yWidth)*yWidth # mm
zLength = math.ceil((zMax - zMin)/zWidth)*zWidth # mm
volume = xLength*yLength*zLength
xOff = xMax - (xLength)/2
yOff = yMax - yLength/2
zOff = zMin
yTiles = int(math.ceil(yLength/yWidth))  #int(round(yLength/yWidth))
zTiles = int(round(zLength/zWidth))
nTiles = zTiles*yTiles*len(wavelengths)
nFrames = int(round(xLength/(xWidth/1000))) #number of frames in X direction


## test to make sure limits are not backwards
if xMin > xMax or yMin > yMax or zMin > zMax:
	sys.exit('--Terminating-- one of the "min" limits is > one of the "max" limits')

print('zTiles = ' + str(zTiles))
print('ytiles = ' + str(yTiles))
# Calculate positions, estimate imaging time,etc.
for j in range(zTiles): 
	for k in range(yTiles):
		for i in range(len(wavelengths)):
			idx = k+j*yTiles+i*yTiles*zTiles
			yPos = yOff- yLength/2.0 + k*yWidth #+ yWidth/2.0
			zPos = j*zWidth + zOff
			# print('idx = ' + str(idx))	
			# print('yPos = ' + str(yPos))
			# print('zPos = ' + str(zPos))
				
print('tissue volume = ' + str(volume) + 'mm^3')
print('number of tiles = ' + str(nTiles))
print('nFrames = ' + str(nFrames))

if binning == '1x1':
	binFactor = 1
elif binning == '2x2':
	binFactor = 2
elif binning == '4x4':
	binFactor = 4

if len(wavelengths) > 1: #check to make sure lasers are listed from red-->blue (just to keep convention consistent)
	if wavelengths[1] > wavelengths[0]:
		sys.exit('List wavelengths in decreasing order (lab convention for ch0 = 660nm')

scantime_singlestrip = xLength/(xWidth*binFactor/expTime)
scantime_theoreticalmaxspeed = xLength/(xWidth*binFactor/1.25)
print('estimated time for imaging = ' + str((scantime_singlestrip+60)*nTiles/3600) + 'hrs')
# print('theoretical imaging time (max speed) = ' + str((scantime_theoreticalmaxspeed)*nTiles/60) + 'minutes')


######### BEGIN SCANNING ##############
# lsmfx_LB.scan3D(drive, fname, xOff, yOff, zOff, xLength, yLength, zLength, xWidth, yWidth, zWidth, yStitchOverlay, zStitchOverlay, camY, camX, expTime, binning, wavelengths, laser_powers,  galvoXoffset, galvoXamp, galvofreq, galvoYoffset, camOffset, flatField)

# print('Copying backup file to Z drive...')
# if copy_to_Xdrive == 'yes':
# 	sys.path.append('Z')
# 	shutil.copytree(drive + ':\\' + fname, 'Z:\\OTLS3_Spring2020_imaging\\Stevens_lab\\' + fname)

