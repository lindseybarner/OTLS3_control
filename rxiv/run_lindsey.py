import ctypes
import ctypes.util
import numpy
import warnings
import os
import os.path
import sys
import time
import lsm20X_batchrun_lindsey as batch
#import write_stitch_macro as wm


############# SCAN PARAMETERS #############
sys.path.append('F')
#drive = 'E'
#base_dir = 'Users//User//Documents//'
drive = 'F'
base_dir = 'Lindsey//'

 ## New session
folder = '11_29_22_20X_test'
fname = base_dir + folder
xMin = 22.44
xMax = 24.76
yMin = 8.76
yMax = 10.25
zMin = -2.00
zMax = -1.98
expTime = 10 #4.99 ms
wavelengths = numpy.array([488]) # lambda in nm
laser_powers = numpy.array([16.5]) #filter 1: 685+ filter 2: LP + single-band filter collects 495-552nm
galvoYoffset =  numpy.array([-1.20]) #for 660nm, 488nm respectively. usually these numbers should be the same for 20X imaging
x = [xMin, xMax]
y = [yMin, yMax]
z = [zMin, zMax]

batch.lsm20X_batchrun_lindsey(drive, folder, x, y, z, expTime, wavelengths, laser_powers, galvoYoffset)
