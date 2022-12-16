laser_LUT_write = {
    'ch1': {    # 561
        'current': [],
        'power': [],
        'zero_current': 1000,
        'measurement_factor': 0.86  # see below
    },
    'ch2': {    # 638
        'current': [],
        'power': [],
        'zero_current': 0,
        'measurement_factor': 0.87
    },
    'ch3': {    # 488
        'current': [1,2,3,4],
        'power': [0,20,50,100],
        'zero_current': 0,
        'measurement_factor': 0.80
    },    
    'ch4': {    # 405
        'current': [],
        'power': [],
        'zero_current': 0,
        'measurement_factor': 0.60
    },
}

with open('skyra_LUT.json', 'w') as write_file:
    json.dump(laser_LUT_write, write_file)

'''
measurement factor is a correction factor between LUT measurements and 
desired power measurements. 0.7 means the desired power measured is 30% 
lower than measurements in LUT, so power setting will be HIGHER than 
input power.

Example usage: LUT is generated directly from fiber. Routine measurements 
from fiber are challenging, so they are instead taken after a collimating 
lens with 70% throughput. Requesting 7mW with 0.7 measurement factor will 
get 10mW power from LUT, so that power after the lens (measurement 
location) is 7mW
'''