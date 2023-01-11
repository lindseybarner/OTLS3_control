import ctypes
import ctypes.util
import numpy
import time
import math
import rs232.RS232 as RS232
import filter_wheel.fw102c_LB as fw102c_LB
import laser.obis as obis
import xyz_stage.ms2000 as ms2000
# import thorlabs_apt as apt
# import generator.ni as generator
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
import serial

ser = serial.Serial('COM9',19200, timeout=0.5, parity=serial.PARITY_NONE, \
	stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, rtscts=1)
s = ser.read(100)
print(s)
ser