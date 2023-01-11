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

import camera.hamamatsu_camera as hc
import rs232.RS232 as RS232
import filter_wheel.fw102c_LB as fw102c_LB
import laser.obis as obis
import xyz_stage.ms2000 as ms2000
import utils.utils as utils
import lsmfx_LB_lasermod
import rewrite_utils
import write_stitch_macro as wsm
import os_system_copy_folder as rapid


############# NEW SAMPLE #############
sys.path.append('C')
drive = 'C'
folder = '5_8_21_5X_OTLS3_V3-2_SYTOX-G_Alexa647'
 
base_dir = 'Users\\User\\Documents\\'
fname = base_dir + folder
source_folder = 'C:\\' + fname + '\\'
copy_to_Zdrive = 'no'
xMin = -2.95	#-1.81
xMax = 8.16 #needs to be at least 2mm i think?
#ycenter = -26.67
yMin = -6.8 ###ycenter - .385
yMax = -0.10 #ycenter +.7
zMin = -3.22 #zcenter - .01
zMax = -1.50 #-2.53 #-2.

# # for ECi 
# xWidth = 0.8457 #0.834 #in um, not mm (2nd gen system 0.48)
# xWidth_ch1 = 0.8457 #.8425 #for 488nm 
# yWidth = 1.69 #1.732 #1.65# 1.708 # mm camera's horizontal FOV
# zWidth = 0.12 #0.151 # mm
# # LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
# yStitchOverlay = 1.695 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
# zStitchOverlay = zWidth #User-defined spacing between image tiles vertically, will affect XML file but not imaging

# for CUBIC n = 1.518
xWidth = 0.8605 #measured with 561nm laser
xWidth_ch1 = 0.8605 #.8425 #for 488nm 
yWidth = 1.72 #1.76 #mm camera's horizontal FOV
zWidth = 0.12 #0.15 #0.151 # mm
# LB added lines below 1/4/20: User-defined spacing between image tiles to optimize stitching. by default they should be xWidth, yWidth, and zWidth
yStitchOverlay = yWidth #1.72 #User-defined spacing between image tiles horizontally, will affect XML file but not imaging
zStitchOverlay = zWidth #User-defined spacing between image tiles vertically, will affect XML file but not imaging



camY = 256 # pixels #"Z" direction, vertical in camera's FOV
camX = 2048 # pixels "Y" direction, horizontal in camera's FOV
expTime = 12 #4.99 ms
camOffset = 0.0 # counts
wavelengths = numpy.array([488,660]) # SWITCHED 488 FILTER SETTING SO THAT IT DOES FILTER 4 9-11-20
laser_powers = numpy.array([2.5,3])
galvoXoffset = 2.57
galvoYoffset = numpy.array([-1.15, -1.15]) #-.025 for 660 #for 660nm, 488nm respectively. usually these numbers are not the same for 5X imaging.
galvoXamp = 6.10 # in V. should be 1.5V for 20X imaging
galvofreq = 1000 #in Hz. rule of thumb should tune to whatever minimum frequency looks "smooth" on the live camera feed
binning = '1x1'#'1x1'
flatField = 0
######### INITIALIZE PARAMETERS ###########
xMin = xMin - .05 #extra room for safety
xMax = xMax #+ .05
yMin = yMin #- yWidth/2#to account for FOV/2 width not accounted for when estimating tissue bounds, + a little extra
yMax = yMax + yWidth#/2


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
imgShape = (nFrames, camY, camX)

#do not set galvo amplitude > 6.2!
if galvoXamp > 7:
	sys.exit('--Terminating-- galvo amplitude too high')

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
			idx_tile = k+j*yTiles
			idx_channel = i
			yPos = yOff- yLength/2.0 + k*yWidth #+ yWidth/2.0
			zPos = j*zWidth + zOff
			# print('j = ' + str(j))
			# print('z = ' + str(zPos))
			# print('idx = ' + str(idx))	
			# print('yPos = ' + str(yPos))
			# print('zPos = ' + str(zPos))


print('Max yPos = ' + str(yPos))
print('Min zPos = ' + str(zPos))
				
print('tissue volume = ' + str(volume) + 'mm^3')
print('number of tiles = ' + str(nTiles))
print('nFrames = ' + str(nFrames))

if binning == '1x1':
	binFactor = 1
elif binning == '2x2':
	binFactor = 2
elif binning == '4x4':
	binFactor = 4

scantime_singlestrip = xLength/(xWidth*binFactor/expTime)
scantime_theoreticalmaxspeed = xLength/(xWidth*binFactor/1.25)
print('estimated time for imaging = ' + str((scantime_singlestrip+60)*nTiles/3600) + 'hrs')
# print('theoretical imaging time (max speed) = ' + str((scantime_theoreticalmaxspeed)*nTiles/60) + 'minutes')

## Estimate memory required for this imaging job
im = numpy.zeros((nFrames,camY,camX), dtype = 'int16')
#Estimate memory required (generously). = memory of all tiles w 10X compression, 1 uncompressed tile in buffer, and multiply by 1.25 for margin
mem_reqd =((im.size*im.itemsize)*nTiles/(1e9*10) + (im.size*im.itemsize)/(1e9))*1.25 #in GB, memory requirement estimated for this job (with 10X compression)
mem_free = (shutil.disk_usage(drive + ':')[2])/1e9 #in GB
del im

#################### #IMAGING ########################################
if mem_free > mem_reqd:
	print('Disk space required = ' + str(mem_reqd) + ' GB')
	print('Disk space in drive = ' + str(mem_free) + ' GB')
	#### BEGIN IMAGING ####
	lsmfx_LB_lasermod.scan3D(drive, fname, xOff, yOff, zOff, xLength, yLength, zLength, xWidth, yWidth, zWidth, yStitchOverlay, zStitchOverlay, camY, camX, expTime, binning, wavelengths, laser_powers,  galvoXoffset, galvoXamp, galvofreq, galvoYoffset, camOffset, flatField)
	# rewrite_utils.write_xml(drive = drive, save_dir = fname, idx = idx, idx_tile = idx_tile, idx_channel = idx_channel, channels = len(wavelengths), camX = camX, camY = camY, tiles_y = yTiles, tiles_z = zTiles, sampling = xWidth, sampling_ch1 = xWidth_ch1, binning = binFactor, offset_y = yStitchOverlay, offset_z = zStitchOverlay, pxshiftYZ = 0, x = imgShape[0], y = imgShape[1], z = imgShape[2])
else: 
	print('LB needs to clear out drive before imaging')


##################################################################################
# #################### OPTIONAL POST-PROCESSING ##################################
##################################################################################

# ### Optional automated post-processing...
print('Copying file to storage drive...')
storage_drive = 'Z'
sys.path.append(storage_drive)

#### Copy data to permanent storage drive
base_dir = 'Lindsey\\\\OTLS3_2021_imaging\\\\breast_cancer_LN\\\\'
destination_folder = storage_drive + ':\\\\' + base_dir + folder + '\\\\'
rapid.copy_folder(source_folder, destination_folder) #this copy method is much faster than shutil.copytree for large files

#### Write and run macro to automatically stitch in ImageJ
wsm.write_macro(storage_drive, base_dir, folder)
wsm.write_bat(storage_drive, base_dir, folder)
wsm.run_bat(storage_drive, base_dir, folder)
## Wait until stitching finishes (data.xml~2 will be written)
file = 'data.xml~2'
while not os.path.exists(destination_folder + file):
	time.sleep(1)
if os.path.exists(destination_folder + file):
	time.sleep(5) #give the file a few seconds to finish writing if needed

#### Run python file that will automatically fuse data frame-by-frame
shutil.copy('Z://Lindsey//OTLS3_2021_imaging//falsecolor_unfused_data//fuse_nuc-cyto_enface.py', destination_folder + '\\fuse.py')
os.chdir(storage_drive + '://' + base_dir + folder)
os.system('python ' + 'fuse.py')

