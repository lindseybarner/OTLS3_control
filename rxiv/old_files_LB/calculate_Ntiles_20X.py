import ctypes
import ctypes.util
import numpy
import time
import math

import utils.utils as utils
# import rclone.rclone as rclone
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


xMin = 31.88
xMax = 32.67
yMin = -5.11
yMax = -2.38
zMin = -2.6
zMax = -2.15 #if these numbers do not make sense, might get error "idx was referenced before assignment"

#Dimensions of FOV
xWidth = 0.20 #in um, not mm (2nd gen system 0.48) 
yWidth = 0.385 # mm camera's horizontal FOV
zWidth = 0.03 #3 # mm calculated based on 610px/125um 11-20-19(2nd gen system 0.07)this will directly change how far z-strips are placed from each otehr in big stitcher
# LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
yStitchOverlay = 0.365 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
zStitchOverlay = .0275 #User-defined spacing between image tiles vertically, will affect XML file but not imaging

camY = 256 # pixels #"Z" direction, vertical in camera's FOV
camX = 2048 # pixels "Y" direction, horizontal in camera's FOV
expTime = 10 #4.99 ms
camOffset = 0.0 # counts
wavelengths = numpy.array([660,488]) # lambda in nm
initial_powers = numpy.array([15,3])
attenuations = numpy.array([1.5,1.5]) # mm^-1
binning = '1x1'
flatField = 0

######### INITIALIZE PARAMETERS ###########
xLength = xMax - xMin # mm
yLength = math.ceil((yMax - yMin)/yWidth)*yWidth # mm
zLength = math.ceil((zMax - zMin)/zWidth)*zWidth # mm
volume = xLength*yLength*zLength
yTiles = int(round(yLength/yWidth))
zTiles = int(round(zLength/zWidth))
nTiles = zTiles*yTiles*len(wavelengths)
print('tissue volume = ' + str(volume) + 'mm^3')
print('number of tiles = ' + str(nTiles))
xOff = xMax - (xLength)/2
yOff = yMax - yLength/2
zOff = zMin