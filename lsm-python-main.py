import lsmfx
import json
import hardware.laser as ls

# import static parameters
with open('static_params.json', 'r') as read_file:
    static_params = json.load(read_file)

camera_dict = static_params['camera']
experiment_dict = static_params['experiment']
daq_dict = static_params['daq']
laser_dict = static_params['laser']
wheel_dict = static_params['wheel']
stage_dict = static_params['stage']
image_wells = static_params['image_wells'] ## Default option for this is "no"


# ------ Set user-defined paramters ------ #

# CAMERA PARAMETERS
camera_dict['expTime'] = 10.0  # ms

# B3D compression. 0.0 = off, 1.0 = standard compression
camera_dict['quantSigma'] = {'405': 1.0,
                             '488': 1.0,
                             '561': 1.0,
                             '660': 1.0}

# FILE PARAMETERS
experiment_dict['drive'] = 'E'
experiment_dict['fname'] = 'scan_well_test'  # file name

# ## If imaging on hivex puck with pre-defined well positions, indicate which wells to image below.
## If not, just comment out the two lines below
image_wells['option'] = 'yes'
image_wells['well_numbers'] = [1,2]

# # ROI PARAMETERS
# experiment_dict['xMin'] = 18.22 # mm
# experiment_dict['xMax'] = 22.08  # mm
# experiment_dict['yMin'] = -10.68  # mm
# experiment_dict['yMax'] = -7.25 # mm
# experiment_dict['zMin'] = -0.93  # mm
# experiment_dict['zMax'] = -0.90  # mm

# Uncomment this line to force no filter on 638 channel (i.e. reflective beads)
# otherwise leave this line commented out
#wheel_dict['names_to_channels']['638'] = 6

# set experiment wavelenths here, power in mW
experiment_dict['wavelengths'] = {'660': 2.0, '488': 2.0}

experiment_dict['attenuations'] = {'405': 1.4,
                                   '488': 1.4,
                                   '561': 1.4,
                                   '660': 1.4}


# NEW: set DAQ parameters to match DAQExpress (values in volts)
# Only ymax & ETL should be adjusted for each sample. Remaining
# parameters should not be changed, but you should confirm they
# match those in DAQExpress

# X Galvo
daq_dict['xmin'] = {'405': 2.99 - 1.90,
                    '488': 2.99 - 1.90,
                    '561': 2.99 - 1.90,
                    '660': 2.99 - 1.90}

daq_dict['xmax'] = {'405': 2.99 + 1.90,
                    '488': 2.99 + 1.90,
                    '561': 2.99 + 1.90,
                    '660': 2.99 + 1.90}

daq_dict['xpp'] = {'405': 1.90,
                   '488': 1.90,
                   '561': 1.90,
                   '660': 1.90}

# Y Galvo
daq_dict['ymin'] = {'405': -1.13,
                    '488': -1.13,
                    '561': -1.13,
                    '660': -1.13}

daq_dict['ymax'] = {'405': -1.13,
                    '488': -1.13,
                    '561': -1.13,
                    '660': -1.13}

daq_dict['ypp'] = {'405': 0.0,
                   '488': 0.0,
                   '561': 0.0,
                   '660': 0.0}


# construct objects
cameraObj = lsmfx.camera(camera_dict)
experimentObj = lsmfx.experiment(experiment_dict)
daqObj = lsmfx.daq(daq_dict)
etlObj = []
laserObj = ls.laser(laser_dict)
wheelObj = lsmfx.wheel(wheel_dict)
stageObj = lsmfx.stage(stage_dict)


lsmfx.scan3D(experimentObj, cameraObj, daqObj, laserObj, wheelObj, etlObj, stageObj, image_wells)