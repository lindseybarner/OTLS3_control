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
import utils.utils as utils
import lsmfx_LB_1tile
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

############# NEW SAMPLE #############
sys.path.append('E')
drive = 'E'
fname = '5_26_20_5X_PSF_ECi_noHivex' # specimen names
copy_to_Xdrive = 'no'
xMin = 6.07
xMax = 7.07 #nFrames/4 must be > 256
yMin = 11.34
yMax = 11.34
zMin = -1.68
zMax = -1.68#if these numbers do not make sense, might get error "idx was referenced before assignment" #if these numbers do not make sense, might get error "idx was referenced before assignment"


# for ECi
xWidth = 0.839 #in um, not mm (2nd gen system 0.48) 
yWidth = 1.65# 1.708 # mm camera's horizontal FOV, minus a little for overlap
zWidth = 0.12 #0.151 # mm calculated based on 610px/125um 11-20-19 
# LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
yStitchOverlay = 1.645 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
zStitchOverlay = zWidth #User-defined spacing between image tiles vertically, will affect XML file but not imaging

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
wavelengths = numpy.array([660]) # #660 NEEDS TO BE FIRST if two-color lambda in nm 
laser_powers = numpy.array([1])
galvoXoffset = 3.43
galvoYoffset = numpy.array([-.75]) #for 660nm, 488nm respectively. usually these numbers are not the same for 5X imaging.
galvoXamp = 5.5 #6.2 # in V. should be 1.5V for 20X imaging
galvofreq = 1000 #in Hz. rule of thumb should tune to whatever minimum frequency looks "smooth" on the live camera feed
binning = '1x1'
flatField = 0
######### INITIALIZE PARAMETERS ###########
xMin = xMin - .05 #extra room for safety
xMax = xMax + .05
yMin = yMin #- yWidth/2#to account for FOV/2 width not accounted for when estimating tissue bounds, + a little extra
yMax = yMax #+ yWidth/2


xLength = xMax - xMin # mm
yLength = yMax - yMin #LB commented math.ceil((yMax - yMin)/yWidth)*yWidth # mm
zLength = math.ceil((zMax - zMin)/zWidth)*zWidth # mm
volume = xLength*yLength*zLength
xOff = xMax - (xLength)/2
yOff = yMax - yLength/2
zOff = zMin
yTiles = int(round(yLength/yWidth)) #LB "math.ceil" used to be "round"
zTiles = int(round(zLength/zWidth))
nTiles = zTiles*yTiles*len(wavelengths)
nFrames = int(round(xLength/(xWidth/1000))) #number of frames in X direction

# print('yLength = ' + str(yLength))
# #print('yMin' + str(yMin))
# #print('yMax' + str(yMax))
# print('yOff' + str(yOff))
for k in range(yTiles): 
	yPos = -yLength/2.0+k*yWidth + yOff
	print('yPos = ' + str(yPos))
print('tissue volume = ' + str(volume) + 'mm^3')
print('number of tiles = ' + str(nTiles))
print('nFrames = ' + str(nFrames))
# print('xOff' + str(xOff))
# print('yOff' + str(yOff))
# print('xLength' + str(xLength))
# print('yLength' + str(yLength))
scantime_singlestrip = xLength/(xWidth/expTime)
print('estimated time for imaging = ' + str((scantime_singlestrip)*nTiles/3600) + 'hrs')
if nFrames/4 < 256:
	sys.exit('--Terminating-- nFrames/4 must be > 256, or downsampling will fail')
########### BEGIN SCANNING ##############
lsmfx_LB_1tile.scan3D(drive, fname, xOff, yOff, zOff, xLength, yLength, zLength, xWidth, yWidth, zWidth, yStitchOverlay, zStitchOverlay, camY, camX, expTime, binning, wavelengths, laser_powers,  galvoXoffset, galvoXamp, galvofreq, galvoYoffset, camOffset, flatField)
##### end of sample
print('Copying backup file to X drive...')
if copy_to_Xdrive == 'yes':
	sys.path.append('X')
	shutil.copytree(drive + ':\\' + fname, 'X:\\' + fname)