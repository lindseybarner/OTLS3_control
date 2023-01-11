
import sys
import time
import rs232.RS232 as RS232
import laser.obis as obis #added LB 1-3-20 so we can turn laser off right after stage stops scanning
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

#laser = obis.Obis(baudrate = 9600, port = 'COM4')
## MS2000
#
# Applied Scientific Instrumentation MS2000 RS232 interface class.
#
class pass_laser:

	def __init__(self,laser):
		self.laser = laser
		print(laser)
		laser.turnOn()

#to make this work, you can do in a separate python command:
# import all the things lines 1-34
#laser = obis.Obis(baudrate = 9600, port = 'COM4')
#import xyz_stage.pass_laser
#then to call it,: xyz_stage.pass_laser.pass_laser(laser)

