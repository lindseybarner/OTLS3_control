import ctypes
import ctypes.util
import numpy
import time
import math
import rs232.RS232 as RS232
import laser.sapphire as sapphire
import laser.obis as obis
import utils.utils as utils
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


for i in range(50):
	try:
		laser = sapphire.SapphireLaser(com = 'COM13')
	except:
		'could not turn on laser. try again'
		pause(2)
		laser = sapphire.SapphireLaser(com = 'COM13')
	laser.setPower(2)
	laser.turnOn()
	laser.turnOff()
	print(laser)
	laser = obis.Obis(baudrate = 9600, port = 'COM12')	
	laser.turnOn()
	laser.turnOff()