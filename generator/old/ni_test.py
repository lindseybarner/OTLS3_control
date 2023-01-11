#!/usr/bin/python
#
# Adam Glaser 07/19
#

import nidaqmx
from nidaqmx import stream_writers
from nidaqmx import constants
import numpy as np
from nidaqmx.types import CtrTime
import threading
import time
import math

class waveformGenerator(object):

	def run(self):

		self.task = nidaqmx.Task()
		#if self.XY == 'Y':
		self.task.ao_channels.add_ao_voltage_chan('Dev1/ao1')
		#if self.XY == 'X':
		self.task.ao_channels.add_ao_voltage_chan('Dev1/ao0')
		self.task.timing.cfg_samp_clk_timing(rate = self.rate, sample_mode = constants.AcquisitionType.CONTINUOUS, samps_per_chan= self.samples)
		writer = stream_writers.AnalogMultiChannelWriter(self.task.out_stream, auto_start = True)
		time = np.linspace(0, 2*math.pi, round(self.rate/self.freq))
		samples = self.amplitude*np.sin(time)+self.offset
		samples = np.vstack((samples,samples))
		print('shape of samples ' + str(samples.shape))
		writer.write_many_sample(samples, timeout = constants.WAIT_INFINITELY)
		self.task.wait_until_done(timeout = constants.WAIT_INFINITELY)
		self.task.stop()
		self.task.close()

	def __init__(self, rate, samples, freq, amplitude, offset, XY): 

		""" Constructor
		:type interval: int
		:param interval: Check interval, in seconds
		"""

		if (samples % 2) != 0:
			samples = samples + 1

		if amplitude > 6:
			amplitude = 0
			print('check amplitude; ni.test preventing amp > 6')

		if abs(offset) > 4:
			offset = 0
			print('check offset; ni.test preventing offset > 4')

		if freq > 1200:
			freq = 1000
			print('check frequency; do not over-run galvo')

		self.XY = XY	
		self.rate = rate
		self.samples = samples
		self.freq = freq
		self.amplitude = amplitude
		self.offset = offset

		self.thread = threading.Thread(target=self.run, args=())
		self.thread.daemon = True
		self._stop = threading.Event() 

	def join(self):
		self.thread.join()

	def start(self):
		self.thread.start()

	def stop(self): 
		self._stop.set()

	def stopped(self): 
		return self._stop.isSet() 