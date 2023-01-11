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

############# SCAN PARAMETERS #############
sys.path.append('E')
drive = 'E'
fname = '5_26_20_20X_PSF_ECi_Hivex_slow3' # specimen names

xMin = -8.3 #scans from - to + 
xMax = -8.1 #needs to be <= 0.2mm 
#ycenter = -26.67
yMin = 5.45 #ycenter - .385
yMax = 5.45 #ycenter +.7
#zcenter = -2.1
zMin = -2.55 #zcenter - .01
zMax = -2.55 #zcenter + .01 #if these numbers do not make sense, might get error "idx was referenced before assignment" #if these numbers do not make sense, might get error "idx was referenced before assignment"

#for ECi
#Dimensions of FOV
xWidth = 0.209 #in um, not mm (2nd gen system 0.48) 
yWidth = 0.385 # mm camera's horizontal FOV
zWidth = 0.03 #3 # mm calculated based on 610px/125um 11-20-19(2nd gen system 0.07)this will directly change how far z-strips are placed from each otehr in big stitcher
# LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
yStitchOverlay = 0.3675 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
zStitchOverlay = .027 #User-defined spacing between image tiles vertically, will affect XML file but not imaging

# #for Clearsee
# xWidth = 0.22779
# yWidth = .467
# zWidth = .04123
# yStitchOverlay = .46 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
# zStitchOverlay = .03 #User-defined spacing between image tiles vertically, will affect XML file but not imaging

camY = 256 # pixels #"Z" direction, vertical in camera's FOV
camX = 2048 # pixels "Y" direction, horizontal in camera's FOV
expTime = 50 #4.99 ms
camOffset = 0.0 # counts
wavelengths = numpy.array([660]) # lambda in nm
laser_powers = numpy.array([0.5]) #filter 1: 685+ filter 2: LP + single-band filter collects 495-552nm
galvoXoffset = 3.43 #in V
galvoYoffset = numpy.array([-.74]) #for 660nm, 488nm respectively. usually these numbers should be the same for 20X imaging

galvoXamp = 6 # in V. should be 1.5V for 20X imaging
galvofreq = 1000 #in Hz. rule of thumb should tune to whatever minimum frequency looks "smooth" on the live camera feed
binning = '1x1'
flatField = 0

######### PARAMETERS ###########
xMin = xMin - .05 #extra room for safety
xMax = xMax + .05
#y min = ymin-ywidth/2 and ymax = ymax + ywidth makes it so that it'll tile 1 tile to the left and right of your center
yMin = yMin #- yWidth/2 #to account for FOV/2 width not accounted for when estimating tissue bounds, + a little extra
yMax = yMax #+ yWidth/2

######### INITIALIZE PARAMETERS ###########
xLength = xMax - xMin # mm
yLength = yMax - yMin #LB commented math.ceil((yMax - yMin)/yWidth)*yWidth # mm
zLength = math.ceil((zMax - zMin)/zWidth)*zWidth # mm
volume = xLength*yLength*zLength
yTiles = int(round(yLength/yWidth)) #LB "math.ceil" used to be "round"
zTiles = int(round(zLength/zWidth))
nTiles = zTiles*yTiles*len(wavelengths)
print('tissue volume = ' + str(volume) + 'mm^3')
print('number of tiles = ' + str(nTiles))
print('folder name = ' + str(fname))
xOff = xMax - (xLength)/2
yOff = yMax - yLength/2
zOff = zMin
nFrames = int(round(xLength/(xWidth/1000))) #number of frames in X direction
####want to make sure that structure at center of coordinates will be imaged at center of FOV
# print('Y positions will be = ')
for j in range(zTiles): 
	for k in range(yTiles):
		yPos = yOff- yLength/2.0 + k*yWidth #+ yWidth/2.0
		print('y = ' + str(yPos))
		zPos = j*zWidth + zOff
		print('z = ' + str(zPos))
print('nFrames = ' + str(nFrames))
scantime_singlestrip = xLength/(xWidth/expTime)
print('estimated time for imaging = ' + str((scantime_singlestrip+60)*nTiles/3600) + 'hrs')

if nFrames/4 < 256:
	sys.exit('--Terminating-- nFrames/4 must be > 256, or downsampling will fail')


############ BEGIN SCANNING ##############
lsmfx_LB_1tile.scan3D(drive, fname, xOff, yOff, zOff, xLength, yLength, zLength, xWidth, yWidth, zWidth, yStitchOverlay, zStitchOverlay, camY, camX, expTime, binning, wavelengths, laser_powers, galvoXoffset, galvoXamp, galvofreq, galvoYoffset, camOffset, flatField)
				
