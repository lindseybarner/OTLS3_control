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
## USED TO WRITE VISUALIZATION FILE (line 308 in lsmfx)

#USED TO WRITE XML FILE (line 331)
def write_xml(drive, save_dir, idx, idx_tile, idx_channel, channels, tiles_y, tiles_z, sampling, binning, offset_y, offset_z, x, y, z):
# old working version: def write_xml(drive, save_dir, idx, idx_tile, idx_channel, channels = 1, tiles_y = 1, tiles_z = 1, sampling = 0.208, binning = 1, offset_y =385, offset_z = 35, x = 1, y = 1, z = 1):
	
	print("Writing BigDataViewer XML file...")
	print('offset_y = ' + str(offset_y))
	c = channels
	tx = tiles_y
	tz = tiles_z
	t = tx*tz
	sx = sampling
	binFactor = binning
	ox = offset_y*1000
	oz = offset_z*1000
	Ntiles = channels*tiles_y*tiles_z
	#idx is the max number registered

	sx = sx
	sy = sx
	sz = sx

	f = open(drive + ':\\' + save_dir + '\\data.xml', 'w')
	f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
	f.write('<SpimData version="0.2">\n')
	f.write('\t<BasePath type="relative">.</BasePath>\n')
	f.write('\t<SequenceDescription>\n')
	f.write('\t\t<ImageLoader format="bdv.hdf5">\n')
	f.write('\t\t\t<hdf5 type="relative">data.h5</hdf5>\n')
	f.write('\t\t</ImageLoader>\n')
	f.write('\t\t<ViewSetups>\n')


	for j in range(0, t):
		for i in range (0, c):
			ind = i+j*c
			if ind <= idx:
				f.write('\t\t\t<ViewSetup>\n')
				f.write('\t\t\t\t<id>' + str(t*i+j) + '</id>\n')
				f.write('\t\t\t\t<name>' + str(t*i+j) + '</name>\n')
				f.write('\t\t\t\t<size>' + str(z) + ' ' + str(y) + ' ' + str(x) + '</size>\n')
				f.write('\t\t\t\t<voxelSize>\n')
				f.write('\t\t\t\t\t<unit>um</unit>\n')
				f.write('\t\t\t\t\t<size>' + str(sx) + ' ' + str(sy) + ' ' + str(sz) + '</size>\n')
				f.write('\t\t\t\t</voxelSize>\n')
				f.write('\t\t\t\t<attributes>\n')
				f.write('\t\t\t\t\t<illumination>0</illumination>\n')
				f.write('\t\t\t\t\t<channel>' + str(i) + '</channel>\n')
				f.write('\t\t\t\t\t<tile>' + str(j) + '</tile>\n')
				f.write('\t\t\t\t\t<angle>0</angle>\n')
				f.write('\t\t\t\t</attributes>\n')
				f.write('\t\t\t</ViewSetup>\n')

	f.write('\t\t\t<Attributes name="illumination">\n')
	f.write('\t\t\t\t<Illumination>\n')
	f.write('\t\t\t\t\t<id>0</id>\n')
	f.write('\t\t\t\t\t<name>0</name>\n')
	f.write('\t\t\t\t</Illumination>\n')
	f.write('\t\t\t</Attributes>\n')
	f.write('\t\t\t<Attributes name="channel">\n')

	for i in range(0, c):
		ind = i
		if ind <= idx_channel:
			f.write('\t\t\t\t<Channel>\n')
			f.write('\t\t\t\t\t<id>' + str(i) + '</id>\n')
			f.write('\t\t\t\t\t<name>' + str(i) + '</name>\n')
			f.write('\t\t\t\t</Channel>\n')

	f.write('\t\t\t</Attributes>\n')
	f.write('\t\t\t<Attributes name="tile">\n')

	for i in range(0, t):
		ind = i
		if ind <= idx_tile:
			f.write('\t\t\t\t<Tile>\n')
			f.write('\t\t\t\t\t<id>' + str(i) + '</id>\n')
			f.write('\t\t\t\t\t<name>' + str(i) + '</name>\n')
			f.write('\t\t\t\t</Tile>\n')

	f.write('\t\t\t</Attributes>\n')
	f.write('\t\t\t<Attributes name="angle">\n')
	f.write('\t\t\t\t<Illumination>\n')
	f.write('\t\t\t\t\t<id>0</id>\n')
	f.write('\t\t\t\t\t<name>0</name>\n')
	f.write('\t\t\t\t</Illumination>\n')
	f.write('\t\t\t</Attributes>\n')
	f.write('\t\t</ViewSetups>\n')
	f.write('\t\t<Timepoints type="pattern">\n')
	f.write('\t\t\t<integerpattern>0</integerpattern>')
	f.write('\t\t</Timepoints>\n')
	f.write('\t\t<MissingViews />\n')
	f.write('\t</SequenceDescription>\n')

	f.write('\t<ViewRegistrations>\n')
	
	for i in range(0, c):
		for j in range(0, tz):
			for k in range(0, tx):

				ind = i*tz*tx + j*tx + k
				#print(ind)

				if ind <= idx/2: #will be true for all ch0 tiles  (idx is max tile, red is 0-max/2)
					transy = -y*j
					transz = -y/math.sqrt(2.0)*j
					shiftx = (ox/sx)*k #LINDSEY CHANGED TO NEGATIVE 11-21-19 IT FIXED STITCHING IN Y DIRECTION (HORIZONTAL CAMERA VIEW)
					shifty = (y/math.sqrt(2.0)-(oz/sz))*j #LINDSEY CHANGED TO NEGATIVE 11-21-19 TRYING TO FIX SHEARING IN X DIRECTION
					#original line above: (y/math.sqrt(2.0)-(oz/sz))*j
					#print('shiftx' + str(shiftx) + 'ind = ' + str(ind))
					f.write('\t\t<ViewRegistration timepoint="0" setup="' + str(ind) + '">\n')
					f.write('\t\t\t<ViewTransform type="affine">\n')
					f.write('\t\t\t\t<Name>Overlap</Name>\n')
					f.write('\t\t\t\t<affine>1.0 0.0 0.0 ' + str(shiftx) + ' 0.0 1.0 0.0 ' + str(shifty) + ' 0.0 0.0 1.0 0.0</affine>\n')
					f.write('\t\t\t</ViewTransform>\n')
					f.write('\t\t\t<ViewTransform type="affine">\n')
					f.write('\t\t\t\t<Name>Deskew</Name>\n')
					f.write('\t\t\t\t<affine>1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0</affine>\n')
					f.write('\t\t\t</ViewTransform>\n')
					f.write('\t\t\t<ViewTransform type="affine">\n')
					f.write('\t\t\t\t<Name>Translation to Regular Grid</Name>\n')
					f.write('\t\t\t\t<affine>1.0 0.0 0.0 0.0 0.0 1.0 0.0 ' + str(transy) + ' 0.0 0.0 1.0 ' + str(transz) + '</affine>\n')
					f.write('\t\t\t</ViewTransform>\n')
					f.write('\t\t</ViewRegistration>\n')

				if ind > idx/2 and ind <= idx: #applies transformation to JUST ch1 tiles
					transy = -y*j
					transz = -y/math.sqrt(2.0)*j
					shiftx = (ox/sx)*k #LINDSEY CHANGED TO NEGATIVE 11-21-19 IT FIXED STITCHING IN Y DIRECTION (HORIZONTAL CAMERA VIEW)
					shifty = (y/math.sqrt(2.0)-(oz/sz))*j #LINDSEY CHANGED TO NEGATIVE 11-21-19 TRYING TO FIX SHEARING IN X DIRECTION
					#original line above: (y/math.sqrt(2.0)-(oz/sz))*j
					#print('shiftx' + str(shiftx) + 'ind = ' + str(ind))
					f.write('\t\t<ViewRegistration timepoint="0" setup="' + str(ind) + '">\n')
					f.write('\t\t\t<ViewTransform type="affine">\n')
					f.write('\t\t\t\t<Name>Overlap</Name>\n')
					f.write('\t\t\t\t<affine>1.0 0.0 0.0 ' + str(shiftx) + ' 0.0 1.0 0.0 ' + str(shifty) + ' 0.0 0.0 1.0 0.0</affine>\n')
					f.write('\t\t\t</ViewTransform>\n')
					f.write('\t\t\t<ViewTransform type="affine">\n')
					f.write('\t\t\t\t<Name>Deskew</Name>\n')
					f.write('\t\t\t\t<affine>1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0</affine>\n')
					f.write('\t\t\t</ViewTransform>\n')
					f.write('\t\t\t<ViewTransform type="affine">\n')
					f.write('\t\t\t\t<Name>Translation to Regular Grid</Name>\n')
					f.write('\t\t\t\t<affine>1.0 0.0 0.0 0.0 0.0 1.0 0.0 ' + str(transy) + ' 0.0 0.0 1.0 ' + str(transz) + '</affine>\n')
					f.write('\t\t\t</ViewTransform>\n')
					f.write('\t\t</ViewRegistration>\n')
					

	f.write('\t</ViewRegistrations>\n')
	f.write('\t<ViewInterestPoints />\n')
	f.write('\t<BoundingBoxes />\n')
	f.write('\t<PointSpreadFunctions />\n')
	f.write('\t<StitchingResults />\n')
	f.write('\t<IntensityAdjustments />\n')
	f.write('</SpimData>')
	f.close()
