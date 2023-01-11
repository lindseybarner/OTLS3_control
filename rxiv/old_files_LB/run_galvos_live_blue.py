#!/usr/bin/python
#


import generator.ni_LB as generator
import time

waveform = generator.waveformGenerator(freq = 1000, Xamplitude =5.5, Xoffset = 2.9, Yamplitude = 0, Yoffset = -1.4) 
waveform.start()