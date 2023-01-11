#!/usr/bin/python
#
# Adam Glaser 07/19
# modified Lindsey Barner 1/2020

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
		self.task.ao_channels.add_ao_voltage_chan('Dev1/ao0')
		self.task.ao_channels.add_ao_voltage_chan('Dev1/ao1')
		#if self.XY == 'X':
		
		self.task.timing.cfg_samp_clk_timing(rate = self.rate, sample_mode = constants.AcquisitionType.CONTINUOUS, samps_per_chan= self.samples)
		writer = stream_writers.AnalogMultiChannelWriter(self.task.out_stream, auto_start = True)

		#configure X galvo
	
		time = np.linspace(0, 2*math.pi, round(self.rate/self.freq))
		samples = self.Xamplitude*np.sin(time)+self.Xoffset
		
		#configure Y galvo
		writer = stream_writers.AnalogMultiChannelWriter(self.task.out_stream, auto_start = True)
		time = np.linspace(0, 2*math.pi, round(self.rate/self.freq))
		Ysamples = self.Yamplitude*np.sin(time)+self.Yoffset
		samples = np.vstack((samples,Ysamples)) #appends second row to samples for Y galvo

		writer.write_many_sample(samples)#, timeout = constants.WAIT_INFINITELY)
		#self.task.wait_until_done(timeout = constants.WAIT_INFINITELY)
		#self.task.stop()
		#self.task.close()

	def __init__(self, freq, Xamplitude, Xoffset, Yamplitude, Yoffset): 
		#X is for X galvo (bottom mirror, lateral scanning), Y is for Y galvo (top mirror, in and out of focus)
		#frequency for X and Y are the same, even though for Y it does not matter b/c amplitude should be zero 

		""" Constructor
		:type interval: int
		:param interval: Check interval, in seconds
		"""

		#if (samples % 2) != 0:
			#samples = samples + 1

		if Xamplitude > 6.2: #or Yamplitude > 0:
			Xamplitude = 0
			Yamplitude = 0
			print('check amplitudes; ni.test prevents Xamplitude > 6.2, and ')

		if abs(Xoffset) > 4 or abs(Yoffset) > 4:
			offset = 0
			print('check offset; ni.test preventing offset > 4')

		if freq > 1200:
			freq = 1000
			print('check frequency; do not over-run galvo')

		self.rate = 100000 #rate
		self.samples = 1 #this will run continuously so doesn't matter#1000000 #samples
		self.freq = freq
		self.Xamplitude = Xamplitude
		self.Xoffset = Xoffset
		self.Yamplitude = Yamplitude
		self.Yoffset = Yoffset

		self.thread = threading.Thread(target=self.run, args=())
		self.thread.daemon = True
		self._stop = threading.Event() 
		self.start()

	def adjust_Yoffset(self,Yoffset):
		self.Yoffset = Yoffset #redefines Y offset
		self.stop() #stops current waveform
		self.run() #re-runs the new modified waveform
		#the "new" waveform can still be stopped the same as the old one
		#i.e., can run "waveform.stop()", or re-run "waveform.adjust_Yoffset(#)" before that

	def adjust_Xoffset(self,Xoffset):
		self.Xoffset = Xoffset #redefines X offset
		self.stop() #stops current waveform
		self.run() #re-runs the new modified waveform
		#the "new" waveform can still be stopped the same as the old one
		#i.e., can run "waveform.stop()", or re-run "waveform.adjust_Yoffset(#)" before that


	def join(self):
		self.thread.join()

	def start(self):
		self.thread.start()

	def stop(self): 
		#self._stop.set()
		#self.stop()
		self.task.close()

	def stopped(self): 
		return self._stop.isSet() 