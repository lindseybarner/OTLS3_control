import ctypes
import ctypes.util
import numpy
import time
import math
import camera.hamamatsu_camera as hc
import lsmfx_LB
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

xMin = 4.5
xMax = 6.5 #needs to be at least 2mm i think?
yMin = 2.0
yMax = 3.8
zMin = -1.83
zMax = -1.80 #if these numbers do not make sense, might get error "idx was referenced before assignment" #if these numbers do not make sense, might get error "idx was referenced before assignment"

xWidth = 0.834 #in um, not mm (2nd gen system 0.48) 
yWidth = 1.65# 1.708 # mm camera's horizontal FOV
zWidth = 0.147 #0.151 # mm calculated based on 610px/125um 11-20-19(2nd gen system 0.07)this will directly change how far z-strips are placed from each otehr in big stitcher
# LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
yStitchOverlay = 1.645 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
zStitchOverlay = .145 #User-defined spacing between image tiles vertically, will affect XML file but not imaging

camY = 256 # pixels #"Z" direction, vertical in camera's FOV
camX = 2048 # pixels "Y" direction, horizontal in camera's FOV
expTime = 2 #4.99 ms
camOffset = 0.0 # counts
wavelengths = numpy.array([660,488]) # lambda in nm
laser_powers = numpy.array([1,1])
galvoXoffset = 2.9
galvoYoffset = numpy.array([-1.45, -1.35]) #for 660nm, 488nm respectively. usually these numbers are not the same for 5X imaging.

galvoXamp = 5.5 # in V. should be 1.5V for 20X imaging
galvofreq = 1000 #in Hz. rule of thumb should tune to whatever minimum frequency looks "smooth" on the live camera feed
binning = '1x1'
flatField = 0


######### INITIALIZE PARAMETERS ###########
xLength = xMax - xMin # mm
yLength = math.ceil((yMax - yMin)/yWidth)*yWidth # mm
zLength = math.ceil((zMax - zMin)/zWidth)*zWidth # mm
volume = xLength*yLength*zLength
xOff = xMax - (xLength)/2
yOff = yMax - yLength/2
zOff = zMin
yTiles = int(round(yLength/yWidth))
zTiles = int(round(zLength/zWidth))
nTiles = zTiles*yTiles*len(wavelengths)
print('tissue volume = ' + str(volume) + 'mm^3')
print('number of tiles = ' + str(nTiles))

if wavelengths.size > 1:
	nWavelengths = len(wavelengths)
else:
	nWavelengths = 1

print('zTiles = ' + str(zTiles))
print('yTiles = ' + str(yTiles))
# for i in range(nWavelengths):
# 	for j in range(zTiles): 
# 		for k in range(yTiles): 
# 			print('k = ' + str(k))
# 			print('j = ' + str(j))
# 			print('i = ' + str(i))
# 			idx = k+j*yTiles+i*yTiles*zTiles
# 			idx_tile = k+j*yTiles
# 			idx_channel = i

# 			print(idx)


for j in range(zTiles): 
	for k in range(yTiles): 
		for i in range(nWavelengths):
			print('k = ' + str(k))
			print('j = ' + str(j))
			print('i = ' + str(i))
			idx = k+j*yTiles+i*yTiles*zTiles
			idx_tile = k+j*yTiles
			idx_channel = i

			print(idx)
