#!/usr/bin/python
#
# Adam Glaser 07/19
# Lindsey Barner edited 1/4/20
import numpy as np
import itertools
from multiprocessing import Pool #  Process pool
from multiprocessing import sharedctypes


def fill_per_window(args):
    window_x, window_y = args
    tmp = np.ctypeslib.as_array(shared_array)

    for idx_x in range(window_x, window_x + block_size):
        for idx_y in range(window_y, window_y + block_size):
            tmp[idx_x, idx_y] = X[idx_x, idx_y]