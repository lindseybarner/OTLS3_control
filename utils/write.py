#!/usr/bin/python
#
# Adam Glaser 07/19
#

import nidaqmx
from nidaqmx import stream_writers
from nidaqmx import constants
from nidaqmx.types import CtrTime
import threading
import time
import math
import numpy
import warnings
import scipy
import h5py
import gc

class writeBDV(object):

	def __init__(self, f, img_3d, idx, binFactor): 

		self.f = f
		self.img_3d = img_3d
		self.idx = idx
		self.binFactor = binFactor

		self.thread = threading.Thread(target=self.run, args=())
		#self.thread.daemon = True

	def run(self):

		res_list = (1, 2, 4, 8)

		res_np = numpy.zeros((len(res_list), 3), dtype = 'float64')
		res_np[:,0] = res_list
		res_np[:,1] = res_list
		res_np[:,2] = res_list
		
		sgroup = self.f.create_group('/s' + str(self.idx).zfill(2))
		resolutions = self.f.require_dataset('/s' + str(self.idx).zfill(2) + '/resolutions', chunks = (res_np.shape), dtype = 'float64', shape = (res_np.shape), data = res_np)

		subdiv_np = numpy.zeros((len(res_list), 3), dtype = 'uint32')

		for z in range(len(res_list)-1, -1, -1):

			chunkSize1 = 256/self.binFactor
			chunkSize2 = 32/self.binFactor
			chunkSize3 = 256/self.binFactor

			res = res_list[z]

			subdiv_np[z, 0] = chunkSize1
			subdiv_np[z, 1] = chunkSize2
			subdiv_np[z, 2] = chunkSize3

			if z != 0:

				print('Writing resolution level ' + str(z))

				resgroup = self.f.create_group('/t00000/s' + str(self.idx).zfill(2) + '/' + str(z))

				with warnings.catch_warnings():
					warnings.simplefilter("ignore")
					img_3d_temp = self.img_3d[0::int(res), 0::int(res), 0::int(res)]
					#img_3d_temp = scipy.ndimage.interpolation.zoom(self.img_3d, float(1.0/res), order = 1, mode = 'nearest')

				# Line below typically reads "dtype = 'int16' " as of September 2020
				data = self.f.require_dataset('/t00000/s' + str(self.idx).zfill(2) + '/' + str(z) + '/cells', chunks = (chunkSize1, chunkSize2, chunkSize3), dtype = 'int16', shape = img_3d_temp.shape, compression_opts=(round(2*1000), 1, round(2.1845*1000), 0, round(1.6*1000)))			
				# Line below (no compression) is typically commented. Uncommenting 10-1-20 for troubleshooting
				# data = f.require_dataset('/t00000/s' + str(idx).zfill(2) + '/' + str(z) + '/cells', chunks = (chunkSize1, chunkSize2, chunkSize3), dtype = 'int16', shape = img_3d_temp.shape)
				data[:] = img_3d_temp

		subdivisions = self.f.require_dataset('/s' + str(self.idx).zfill(2) + '/subdivisions', chunks = (res_np.shape), dtype = 'uint32', shape = (subdiv_np.shape), data = subdiv_np)
		
		del self.img_3d
		del img_3d_temp
		
		gc.collect()

	def start(self):
		self.thread.start()

	def join(self):
		self.thread.join()

	def alive(self):
		flag = self.thread.isAlive()
		return flag