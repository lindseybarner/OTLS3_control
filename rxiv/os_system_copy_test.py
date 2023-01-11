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

 #copy a folder and contents using os.system (much faster than shutil.copytree for large files)
def copy_folder(source_folder, destination_folder):
	if os.path.exists(destination_folder):
		sys.exit('destination folder already exists')
	os.makedirs(destination_folder)
	for file in os.listdir(source_folder):
		print(file)
		os.system('copy ' + source_folder + file + ' ' + destination_folder + file)

