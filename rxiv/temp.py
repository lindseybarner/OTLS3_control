
import time
import math
import numpy
import warnings
import scipy
import h5py
import gc


# def add():
# 	y = 3 + 3
# 	print('adding')
# 	return y


# 	### python

def fxn(name):
	print('starting thread')
	time.sleep(15)
	print('finishing thread')

write_threads = []

current_thread = threading.Thread(target = fxn, args = (1,))
write_threads.append(current_thread)
current_thread.start()

current_thread = threading.Thread(target = fxn, args = (1,))
write_threads.append(current_thread)
current_thread.start()

previous_thread = write_threads[0:1 + 1]
previous_thread[0].isAlive()