import ctypes
import ctypes.util
import numpy
import time
import math
#import camera.hamamatsu_camera as hc
import rs232.RS232 as RS232
import filter_wheel.fw102c_LB as fw102c
# import laser.skyra as skyra
# import xyz_stage.ms2000 as ms2000
#import thorlabs_apt as apt #don't think i need this? for thorlabs motor in lsfmx.py
#import generator.ni as generator
# import utils.findbounds as findbounds
# import utils.chromatic as chromatic
# import utils.utils as utils
# import rclone.rclone as rclone
import lsmfx_LB as lsmfx_LB
import h5py
# import warnings
import os
import os.path
# import errno
# import sys
# import scipy.ndimage
# import warnings
# import gc
# import nidaqmx
# import os
# import os.path
# from os import path
# import shutil

############# SCAN PARAMETERS #############
drive = 'C'
fname = '11-25-19_scan1_ECi_TOPRO3_prostate' # specimen names

xcenter = 7.62
ycenter = 1.92
zcenter = -3.27
xMin = xcenter - .0528 #2 #2MM BY 2MM BY 200UM
xMax = xcenter + 0.0 #.2
yMin = ycenter - 0.0
yMax = ycenter + 0.4
zMin = zcenter - 0.
zMax = zcenter + 0.03

xWidth = 0.20 #in um, not mm (2nd gen system 0.48) 
yWidth = 0.37 # mm (2nd gen system 0.8)
zWidth = 0.03 # mm calculated based on 610px/125um 11-20-19(2nd gen system 0.07)
camY = 256 # pixels #"Z" direction, vertical in camera's FOV
camX = 2048 # pixels "Y" direction, horizontal in camera's FOV
expTime = 4.99 # ms
camOffset = 0.0 # counts
wavelengths = numpy.array([660]) # lambda in nm
motor_positions = numpy.array([5.75, 1.60])
initial_powers = numpy.array([25])
attenuations = numpy.array([1.5,1.5]) # mm^-1
binning = '1x1'
flatField = 0
#motor_positions = numpy.array([7.55, 5.75, 1.60])

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

############ BEGIN SCANNING ##############
lsmfx_LB.scan3D(drive, fname, xOff, yOff, zOff, xLength, yLength, zLength, xWidth, yWidth, zWidth, camY, camX, expTime, binning, wavelengths, initial_powers, motor_positions, attenuations, camOffset, flatField)