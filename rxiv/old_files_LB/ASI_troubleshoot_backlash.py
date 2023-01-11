#!/usr/bin/python
#

# import imagej
# ij = imagej.init('C:\\Users\\AERB\\Documents\\Fiji.app', headless = False)
# from imglyb import util

# from jnius import autoclass
# spimData = autoclass('bdv.spimdata.SpimDataMinimal')
# spimXML = autoclass('bdv.spimdata.XmlIoSpimDataMinimal')
# bdvWindow = autoclass('bdv.util.BdvFunctions')

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
# import thorlabs_apt as apt
import generator.ni_LB as generator
# import utils.findbounds as findbounds
import utils.utils as utils
import utils.background as background
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
from os import path
import shutil
import logging
import tifffile

xyzStage = ms2000.MS2000(baudrate = 9600, port = 'COM5')
xyzStage.setScanF(1)
xyzStage.setBacklash(0)
xyzStage.setTTL(0)
initialPos = xyzStage.getPosition()
print(xyzStage)


xyzStage.setVelocity('X',0.05) #used to be .5
xyzStage.setVelocity('Y',0.05) #used to be .5
xyzStage.setVelocity('Z',0.05) #used to be .5
xyzStage.goAbsolute('X', 0, False)
xyzsStage.setVelocity('X',.05)
xyzStage.setScanR(0, 1)
xyzStage.setScanV(0)