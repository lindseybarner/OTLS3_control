#!/usr/bin/python


import numpy
import time
import math
import h5py
import warnings
import falsecolor as fc
import tifffile
import threading
import utils.utils_singleprocessing as utils_singleprocessing
import numpy as np


class fc_h5(object):

	def __init__(self, data_ch0, data, idx_ch0, camY, binZ, nFrames, nTiles, chunkSize1, chunkSize2, chunkSize3, imgShape_fc): 

		# self.f_fc = f_fc
		self.data_ch0 = data_ch0
		self.data = data
		self.idx_ch0 = idx_ch0
		# self.data_fc_0 = data_fc_0
		# self.data_fc_1 = data_fc_1
		# self.data_fc_2 = data_fc_2
		self.camY = camY
		self.binZ = binZ
		self.nFrames = nFrames
		self.nTiles = nTiles
		self.chunkSize1 = chunkSize1
		self.chunkSize2 = chunkSize2
		self.chunkSize3 = chunkSize3
		self.imgShape_fc = imgShape_fc


		############## SETUP FALSECOLOR SETTINGS #################
		settings_dict = fc.getDefaultRGBSettings(use_default=True) #this stores settings for either nuclei or cyto
		self.nuclei_RGBsettings = settings_dict['nuclei']
		self.cyto_RGBsettings = settings_dict['cyto']
		self.nuc_normfactor = 5500
		self.cyto_normfactor = 60700

		self.run()
		# self.thread = threading.Thread(target=self.run, args=())


	def run(self):
		f_fc = h5py.File('data_fc.h5','a')
		tgroup_fc = f_fc.create_group('/t00000')
			# data_fc_1 = self.f_fc.require_dataset('/t00000/s' + str(self.idx_ch0 + self.nTiles*1).zfill(2) + '/' + str(0) + '/cells', chunks = (self.chunkSize1, int(self.chunkSize2/4), self.chunkSize3), dtype = 'uint8', shape = self.imgShape_fc)
		# data_fc_2 = self.f_fc.require_dataset('/t00000/s' + str(self.idx_ch0 + self.nTiles*2).zfill(2) + '/' + str(0) + '/cells', chunks = (self.chunkSize1, int(self.chunkSize2/4), self.chunkSize3), dtype = 'uint8', shape = self.imgShape_fc)

		im_3d = np.zeros((self.nFrames,int(self.camY/self.binZ),2048,3), dtype = 'uint8')
		z_fc = 0
		for z in range(0, self.camY, self.binZ):
			im = fc.rapidFalseColor(self.data_ch0[:,z,:], self.data[:,z,:], self.nuclei_RGBsettings, self.cyto_RGBsettings, 
			        run_FlatField_cyto = False, run_FlatField_nuc = False, cyto_normfactor = self.cyto_normfactor, 
			        nuc_normfactor = self.nuc_normfactor, cyto_bg_threshold = 150, nuc_bg_threshold = 150, LBthresh = 'on')
			tifffile.imwrite('test.tif', im)
			# data_fc_0[:,z_fc,:] = im[:,:,0] #Write R to channel 0 
			# data_fc_1[:,z_fc,:] = im[:,:,2] # Write G to channel "2"
			# data_fc_2[:,z_fc,:] = im[:,:,1] # Write B to channel "1"
			im_3d[:,z_fc,:,:] = im
			z_fc += 1

		for color in range(3):
			resgroup_fc = f_fc.create_group('/t00000/s' + str(self.idx_ch0 + self.nTiles*color).zfill(2) + '/' + str(0))

		data_fc = f_fc.require_dataset('/t00000/s' + str(self.idx_ch0 + self.nTiles*0).zfill(2) + '/' + str(0) + '/cells', chunks = (self.chunkSize1, int(self.chunkSize2/4), self.chunkSize3), dtype = 'uint8', shape = self.imgShape_fc)
		data_fc = im_3d[:,:,:,0]
		data_fc = f_fc.require_dataset('/t00000/s' + str(self.idx_ch0 + self.nTiles*1).zfill(2) + '/' + str(0) + '/cells', chunks = (self.chunkSize1, int(self.chunkSize2/4), self.chunkSize3), dtype = 'uint8', shape = self.imgShape_fc)
		data_fc = im_3d[:,:,:,2]
		data_fc = f_fc.require_dataset('/t00000/s' + str(self.idx_ch0 + self.nTiles*2).zfill(2) + '/' + str(0) + '/cells', chunks = (self.chunkSize1, int(self.chunkSize2/4), self.chunkSize3), dtype = 'uint8', shape = self.imgShape_fc)
		data_fc = im_3d[:,:,:,1]

		for color in range(3):
			print('writing downsampled resolution for idx = ' + str(self.idx_ch0 + self.nTiles*color))
			utils_singleprocessing.writeBDV_fc(f_fc, im_3d[:,:,:,color], self.idx_ch0 + self.nTiles*color, 1)

		# return im_3d

	# def start(self):
	# 	self.thread.start()

	# def join(self):
	# 	self.thread.join()

	# def alive(self):
	# 	flag = self.thread.isAlive()
	# 	return flag


# class fc_h5(object):

# 	def __init__(self, data, data_fc, camY, zBin): 

# 		self.data = data
# 		self.data_fc = data_fc
# 		self.camY = camY
# 		self.zBin = zBin
# 		self.thread = threading.Thread(target=self.run, args=())

# 	def run(self):
# 		############## SETUP FALSECOLOR SETTINGS #################
# 		settings_dict = fc.getDefaultRGBSettings(use_default=True) #this stores settings for either nuclei or cyto
# 		nuclei_RGBsettings = settings_dict['nuclei']
# 		cyto_RGBsettings = settings_dict['cyto']
# 		nuc_normfactor = 5500
# 		cyto_normfactor = 60700

# 		z_fc = 0
# 		for z in range(0, self.camY, self.zBin):
# 			self.data_fc[:,z_fc,:] = fc.rapidFalseColor(self.data[:,z,:], self.data[:,z,:], nuclei_RGBsettings, cyto_RGBsettings, 
# 			        run_FlatField_cyto = False, run_FlatField_nuc = False, cyto_normfactor = cyto_normfactor, 
# 			        nuc_normfactor = nuc_normfactor, cyto_bg_threshold = 150, nuc_bg_threshold = 150, LBthresh = 'on')[:,:,0] 
# 			z_fc += 1
# 		# return data_fc

# 	def start(self):
# 		self.thread.start()

# 	def join(self):
# 		self.thread.join()

# 	def alive(self):
# 		flag = self.thread.isAlive()
# 		return flag