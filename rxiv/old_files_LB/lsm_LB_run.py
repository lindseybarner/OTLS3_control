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
# import utils.findbounds as findbounds
# import utils.chromatic as chromatic
import utils.utils as utils
# import rclone.rclone as rclone
import lsmfx_LB as lsmfx_LB
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
sys.path.append('Y')
drive = 'Y'
fname = '12-15-19_OTLS3_Au_PSF_ECi_10msexp' # specimen names

xcenter = 52.07
ycenter = -4.03
zcenter = -3.701
xMin = xcenter - 0.25 #2 #2MM BY 2MM BY 200UM
xMax = xcenter + 0.25 #.2
yMin = ycenter - .35
yMax = ycenter + 00
zMin = zcenter - 0.00
zMax = zcenter + 0.033

# xMin = 51.57
# xMax = 52.57
# yMin = .75
# yMax = 1.5
# zMin = -2.15
# zMax = -2.00

xWidth = 0.20 #in um, not mm (2nd gen system 0.48) 
yWidth = 0.35 # mm camera's horizontal FOV
zWidth = 0.033 # mm calculated based on 610px/125um 11-20-19(2nd gen system 0.07)this will directly change how far z-strips are placed from each otehr in big stitcher
camY = 256 # pixels #"Z" direction, vertical in camera's FOV
camX = 2048 # pixels "Y" direction, horizontal in camera's FOV
expTime = 5 #4.99 ms
camOffset = 0.0 # counts
wavelengths = numpy.array([660]) # lambda in nm
initial_powers = numpy.array([1])
attenuations = numpy.array([1.5,1.5]) # mm^-1
binning = '1x1'
flatField = 0
motor_positions = numpy.array([5.75, 1.60])
# xMin = xMin - 0.5
# xMax = xMax + 0.5 
# yMin = yMin - 0.5
# yMax = yMax + 0.5

######### INITIALIZE PARAMETERS ###########
xLength = xMax - xMin # mm
yLength = math.ceil((yMax - yMin)/yWidth)*yWidth # mm
zLength = math.ceil((zMax - zMin)/zWidth)*zWidth # mm
xOff = xMax - (xLength)/2
yOff = yMax - yLength/2
zOff = zMin

####### SAVE PYTHON FILES TO FOLDER FOR RECORD##########



############ BEGIN SCANNING ##############
lsmfx_LB.scan3D(drive, fname, xOff, yOff, zOff, xLength, yLength, zLength, xWidth, yWidth, zWidth, camY, camX, expTime, binning, wavelengths, initial_powers, motor_positions, attenuations, camOffset, flatField)