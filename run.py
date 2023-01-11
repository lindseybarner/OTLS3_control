import ctypes
import ctypes.util
import numpy
import warnings
import os
import os.path
import sys
import time
import lsm20X_batchrun as batch
#import write_stitch_macro as wm


############# SCAN PARAMETERS #############
sys.path.append('F')
#drive = 'E'
#base_dir = 'Users//User//Documents//'
drive = 'F'
base_dir = 'Gan//'

 ## New session
folder = '10_25_22_20X_SU-16-13697C1-a-flip'
fname = base_dir + folder
xMin = 23.99
xMax = 27.46
yMin = -13.48
yMax = -10.77
zMin = -2.66
zMax = -2.31
expTime = 10 #4.99 ms
wavelengths = numpy.array([660,488]) # lambda in nm
laser_powers = numpy.array([1.0, 2.0]) #filter 1: 685+ filter 2: LP + single-band filter collects 495-552nm
galvoYoffset =  numpy.array([-1.15, -1.15]) #for 660nm, 488nm respectively. usually these numbers should be the same for 20X imaging
x = [xMin, xMax]
y = [yMin, yMax]
z = [zMin, zMax]

batch.lsm20X_batchrun(drive, folder, x, y, z, expTime, wavelengths, laser_powers, galvoYoffset)

# # Commands to automatically write a clickable bat file to stitch the dataset
# dest_drive = 'Y'
# dest_base = 'Lindsey//OTLS3_2022_imaging//esophagus//8183G'
# wm.write_macro(dest_drive, dest_base, folder)
# wm.write_bat(dest_drive, dest_base, folder)

 ## New session
folder = '10_25_22_20X_SU-16-04924B1-a'
fname = base_dir + folder
xMin = 25.91
xMax = 28.65
yMin = 0.36
yMax = 4.21
zMin = -2.64
zMax = -2.44
expTime = 10 #4.99 ms
wavelengths = numpy.array([660,488]) # lambda in nm
laser_powers = numpy.array([1.0, 4.0]) #filter 1: 685+ filter 2: LP + single-band filter collects 495-552nm
galvoYoffset =  numpy.array([-1.15, -1.15]) #for 660nm, 488nm respectively. usually these numbers should be the same for 20X imaging
x = [xMin, xMax]
y = [yMin, yMax]
z = [zMin, zMax]

batch.lsm20X_batchrun(drive, folder, x, y, z, expTime, wavelengths, laser_powers, galvoYoffset)
