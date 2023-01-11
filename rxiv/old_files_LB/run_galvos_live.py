#!/usr/bin/python
#


import generator.ni as generator
import time

def align_beam():
	waveformX = generator.waveformGenerator(rate = 100000, samples = 1, freq = 1, amplitude = 0, offset = 2.0, XY = 'X')
	waveformX.start()
	waveformY.stop()
	waveformY = generator.waveformGenerator(rate = 100000, samples = 1, freq = 1, amplitude = 0, offset = -1.5, XY = 'Y')
	waveformY.start()
	waveformY.stop()

def on():
	waveformY = generator.waveformGenerator(rate = 100000, samples = 1, freq = 1, amplitude = 0, offset = -1.5, XY = 'Y')
	waveformY.start()
	waveformY.stop()

	waveformX = generator.waveformGenerator(rate = 100000, samples = 1000000, freq = .1, amplitude = 1.5, offset = 2.8, XY = 'X')
	waveformX.start()
	waveformX.stop()


def user_input():
	n = None
	while n != 'stop':
		waveformX = generator.waveformGenerator(rate = 100000, samples = 1000000, freq = .1, amplitude = 1.5, offset = 2.8, XY = 'X')
		#waveformY = generator.waveformGenerator(rate = 100000, samples = 1, freq = 1, amplitude = 0, offset = -1.5, XY = 'Y')
		waveformX.start()
		time.sleep(0.5)
		waveformX.stop()
		time.sleep(0.5)
		#waveformY.start()
		#n = input('stop')
	else:
		print(str(n))

	#n = input('hit any key to stop running galvos')
	#if n = 
