
import numpy as np
import math
import h5py
import os.path
import sys
import skimage.transform
# import pco
import hardware.hamamatsu as hc
# Tiger or MS2000 are imported below based on stage model param
import hardware.ni as ni
import hardware.fw102c as fw102c
import hardware.laser as ls
import hardware.skyra as skyra
import hardware.obis as obis
# import hardware.sapphire as sapphire
from hardware.opto import Opto
import h5
import time as timer
import shutil
import hivex_puck as puck


class experiment(object):

    def __init__(self, experiment_dict):

        self.drive = experiment_dict['drive']
        self.fname = experiment_dict['fname']
        self.xWidth = experiment_dict['xWidth']
        self.yWidth = experiment_dict['yWidth']
        self.zWidth = experiment_dict['zWidth']
        self.wavelengths = experiment_dict['wavelengths']
        self.attenuations = experiment_dict['attenuations']
        self.theta = experiment_dict['theta']
        self.overlapY = experiment_dict['overlapY']
        self.overlapZ = experiment_dict['overlapZ']

        ## If imaging pre-defined coordinates for hivex well, these keys will not be defined until lsmfx is opened 
        check_for_keys = 'xMin', 'xMax', 'yMin', 'yMax', 'zMin', 'zMax'
        for item in check_for_keys:
	        if item in experiment_dict:
	            self.xMin = experiment_dict['xMin']
	            self.xMax = experiment_dict['xMax']
	            self.yMin = experiment_dict['yMin']
	            self.yMax = experiment_dict['yMax']
	            self.zMin = experiment_dict['zMin']
	            self.zMax = experiment_dict['zMax']
	            # print('defined all experiment_dict keys')
	        else:
	        	pass


class scan(object):
    def __init__(self, experiment, camera):

        self.xLength = experiment.xMax - experiment.xMin  # mm
        self.yLength = round((experiment.yMax - experiment.yMin) /
                             experiment.yWidth) * experiment.yWidth  # mm
        self.zLength = round((experiment.zMax - experiment.zMin) /
                             experiment.zWidth) * experiment.zWidth  # mm
        self.xOff = experiment.xMax - self.xLength/2
        self.yOff = experiment.yMax - self.yLength/2
        self.zOff = experiment.zMin
        self.nFrames = int(np.floor(self.xLength/(experiment.xWidth/1000.0)))
        self.nWavelengths = len(experiment.wavelengths)
        self.yTiles = int(round(self.yLength/experiment.yWidth))
        self.zTiles = int(round(self.zLength/experiment.zWidth))

        # setup scan speed and chunk sizes
        self.scanSpeed = self.setScanSpeed(experiment.xWidth, camera.expTime)
        self.chunkSize1 = 256
        if self.chunkSize1 >= self.nFrames/8:
            self.chunkSize1 = np.floor(self.nFrames/8)

        self.chunkSize2 = 16

        if self.chunkSize2 >= camera.Y/8:
            self.chunkSize2 = np.floor(camera.Y/8)

        self.chunkSize3 = 256
        if self.chunkSize3 >= camera.X/8:
            self.chunkSize3 = np.floor(camera.X/8)

        self.blockSize = int(2*self.chunkSize1)

    def setScanSpeed(self, xWidth, expTime):

        speed = xWidth/(1.0/(1.0/((expTime + 10.0e-3)/1000.0))*1000.0)
        return speed


# TODO: Change name to camera_settings
class camera(object):
    def __init__(self, camera_dict):
        self.number = camera_dict['number']
        self.X = camera_dict['X']
        self.Y = camera_dict['Y']
        self.sampling = camera_dict['sampling']
        self.expTime = camera_dict['expTime']
        self.triggerMode = camera_dict['triggerMode']
        self.acquireMode = camera_dict['acquireMode']
        self.shutterMode = camera_dict['shutterMode']
        self.compressionMode = camera_dict['compressionMode']
        self.B3Denv = camera_dict['B3Denv']
        self.quantSigma = camera_dict['quantSigma']
        self.camtype = camera_dict['type']

    def initialize(self, camera_dict):
        if self.camtype == 'pco':
            cam = pco.Camera(camera_number=self.number)

            cam.configuration = {'exposure time': self.expTime*1.0e-3,
                                 'roi': (1,
                                         1023-round(self.Y/2),
                                         2060,
                                         1026+round(self.Y/2)),
                                 'trigger': self.triggerMode,
                                 'acquire': self.acquireMode,
                                 'pixel rate': 272250000}

            cam.record(number_of_images=self.nFrames, mode='sequence non blocking')

            ring_buffer = np.zeros((session.blockSize,
                                   self.Y,
                                   self.X),
                                   dtype=np.uint16)
            return cam


class daq(object):
    def __init__(self, daq_dict):

        self.rate = daq_dict['rate']
        self.board = daq_dict['board']
        # self.name = daq_dict['name']
        self.num_channels = daq_dict['num_channels']
        self.names_to_channels = daq_dict['names_to_channels']

        self.xmin = daq_dict['xmin']
        self.xmax = daq_dict['xmax']
        self.xpp = daq_dict['xpp']
        self.ymin = daq_dict['ymin']
        self.ymax = daq_dict['ymax']
        self.ypp = daq_dict['ypp']


class etl(object):
    def __init__(self,
                 etl_dict):
        self.port = etl_dict['port']


class wheel(object):
    def __init__(self,
                 wheel_dict):
        self.port = wheel_dict['port']
        self.rate = wheel_dict['rate']
        self.names_to_channels = wheel_dict['names_to_channels']


class stage(object):
    def __init__(self,
                 stage_dict):
        self.port = stage_dict['port']
        self.rate = stage_dict['rate']
        self.model = stage_dict['model']

        # Should check the velocity and acceration, I think this
        # really shouldn't be part of the init since it's set to different
        # values in various places
        self.settings = {'backlash': 0.0,
                         'velocity': 1.0,
                         'acceleration': 100
                         }
        self.axes = ('X', 'Y', 'Z')

    def initialize(self):

        if self.model == 'tiger':
            print('initializing stage: Tiger')
            import hardware.tiger as tiger
            xyzStage = tiger.TIGER(baudrate=self.rate, port=self.port)
            xyzStage.setPLCPreset(6, 52)

        elif self.model == 'ms2000':
            print('initializing stage: MS2000')
            import hardware.ms2000 as ms2000
            xyzStage = ms2000.MS2000(baudrate=self.rate, port=self.port)
            xyzStage.setTTL('Y', 3)

        else:
            raise Exception('invalid stage type!')

        initialPos = xyzStage.getPosition()
        xyzStage.setScanF(1)
        for ax in self.axes:
            xyzStage.setBacklash(ax, self.settings['backlash'])
            xyzStage.setVelocity(ax, self.settings['velocity'])
            xyzStage.setAcceleration(ax, self.settings['acceleration'])
        print('stage initialized', initialPos)
        return xyzStage, initialPos



def scan3D_image_wells(experiment, camera, daq, laser, wheel, etl, stage, image_wells):

    if image_wells['option'] == 'yes':
        experiment.fname += '_well_N' ## re-format file name for well-based imaging

        ## Check to make sure that well numbers were defined by the user
        try:
           image_wells['well_numbers']
        except NameError:
            print('Well numbers are not defined')

        for well_number in image_wells['well_numbers']:
            experiment = puck.well(well_number, experiment) ## Define imaging coordinates for this well
            fname_end = str(experiment.fname).split('_')[-1]
            experiment.fname = experiment.fname.replace(fname_end, str(well_number)) ## adjust fname
            # ROUND SCAN DIMENSIONS & SETUP IMAGING SESSION
            session = scan(experiment, camera)

            # SETUP DATA DIRECTORY
            ## Check if drive already exists. If so, provide option to delete
            if os.path.exists(experiment.drive + ':\\' + experiment.fname):
                userinput = input('this file directory already exists! permanently delete? [y/n]')
                if userinput == 'y':
                    shutil.rmtree(experiment.drive + ':\\' + experiment.fname, ignore_errors=True)
                if userinput== 'n':
                    sys.exit('--Terminating-- re-name write directory and try again')

            os.makedirs(experiment.drive + ':\\' + experiment.fname)
            dest = experiment.drive + ':\\' + experiment.fname + '\\data.h5'

            #  CONNECT XYZ STAGE
            xyzStage, initialPos = stage.initialize()

            #  INITIALIZE H5 FILE
            h5.h5init(dest, camera, session, experiment)
            h5.write_xml(experiment=experiment, camera=camera, scan=session)

            # CONNECT NIDAQ
            waveformGenerator = ni.waveformGenerator(daq=daq,
                                                     camera=camera,
                                                     triggered=False)

            # CONNECT LASER

            # according to the manual, you should wait for 2min after setting
            # laser 1 (561) to mod mode for power to stabalize. Consider adding this in
            # TODO: disentangle laser and experiment attributes
            
            # Laser = laser.initialize(experiment, session) ## For Cobolt on OTLS-4
            Laser = dict()
            for ch in range(session.nWavelengths):
                wave_str = list(experiment.wavelengths)[ch]
                Laser[wave_str] = laser.initialize(experiment, session, laser.models[wave_str], laser.ports[wave_str])


            # CONNECT FILTER WHEEL

            fWheel = fw102c.FW102C(baudrate=wheel.rate, port=wheel.port)

            # CONNECT CAMERA
            # TODO: setup separate hardware initialization method within camera
            print(camera)
            # cam = camera.initialize(camera)
            hcam = hc.HamamatsuCameraMR(camera_id=0)

            # Set camera properties
            hcam.setPropertyValue("defect_correct_mode", "OFF") # keep defect mode on
            hcam.setPropertyValue("readout_speed", 2) # 1 or 2. 2 is fastest mode
            hcam.setPropertyValue("exposure_time", camera.expTime/1000.0) # convert from msec to sec
            hcam.setPropertyValue("subarray_hsize", camera.X)
            hcam.setPropertyValue("subarray_vsize", camera.Y)
            hcam.setPropertyValue("subarray_vpos", 1024-camera.Y/2)
            hcam.setPropertyValue("binning", 1) #binFactor)

            # Set trigger properties
            hcam.setPropertyValue("trigger_source", 'INTERNAL') # 1 (internal), 2 (external), 3 (software)
            hcam.setPropertyValue("trigger_mode", 'START') # 1 (normal), 6 (start)
            hcam.setPropertyValue("trigger_active", 'EDGE') # 1 (edge), 2 (level), 3 (syncreadout)
            hcam.setPropertyValue("trigger_polarity", 'POSITIVE') # 1 (negative), 2 (positive)
            print('nframes = ' + str(session.nFrames))
            hcam.setACQMode("fixed_length",session.nFrames)


            # print('made ring buffer')
            tile = 0
            previous_tile_time = 0
            previous_ram = 0

            start_time = timer.time()

            xPos = session.xLength/2.0 - session.xOff

            for j in range(session.zTiles):

                zPos = j*experiment.zWidth + session.zOff
                xyzStage.setVelocity('Z', 0.1)
                xyzStage.goAbsolute('Z', zPos, False)

                for k in range(session.yTiles):

                    yPos = session.yOff - session.yLength / 2.0 + \
                        k*experiment.yWidth + experiment.yWidth / 2.0

                    xyzStage.setVelocity('Y', 1.0)
                    xyzStage.goAbsolute('Y', yPos, False)

                    for ch in range(session.nWavelengths):

                        wave_str = list(experiment.wavelengths)[ch]
                        # wave_str is wavelength in nm as a string, e.g. '488'

                        # ch is order of wavelenghts in main (an integer 0 -> X)
                        #   (NOT necessarily Skyra channel number)

                        xyzStage.setVelocity('X', 1.0)
                        xPos = session.xLength/2.0 - session.xOff
                        xyzStage.goAbsolute('X', -xPos, False)

                        # CHANGE FILTER

                        fWheel.setPosition(wheel.names_to_channels[wave_str])

                        # START SCAN
                        Laser[wave_str].setPower(experiment.wavelengths[wave_str]) ## Set power of laser

                        # skyraLaser.setModulationHighCurrent(
                        #     laser.names_to_channels[wave_str],
                        #     experiment.wavelengths[wave_str] /
                        #     np.exp(-j*experiment.zWidth /
                        #            experiment.attenuations[wave_str])
                        #     )
                        print('finish code to write voltages in DAQ')
                        voltages, rep_time = write_voltages(daq=daq,
                                                            laser=laser,
                                                            camera=camera,
                                                            experiment=experiment,
                                                            ch=ch)

                        waveformGenerator.ao_task.write(voltages)

                        print('Starting tile ' + str((tile)*session.nWavelengths+ch+1),
                              '/',
                              str(session.nWavelengths*session.zTiles*session.yTiles))
                        print('y position: ' + str(yPos) + ' mm')
                        print('z position: ' + str(zPos) + ' mm')
                        tile_start_time = timer.time()

                        xyzStage.setScanR(-xPos, -xPos + session.xLength)
                        xyzStage.setScanV(yPos)

                        response = xyzStage.getMotorStatus()
                        while response[0] == 'B':
                            response = xyzStage.getMotorStatus()

                        xyzStage.setVelocity('X', session.scanSpeed)
                        xyzStage.setVelocity('Y', session.scanSpeed)
                        xyzStage.setVelocity('Z', session.scanSpeed)

                        waveformGenerator.ao_task.start()
                        # cam.start() ## For pco camera
                        hcam.startAcquisition() ## For hamamatsu camera
                        xyzStage.scan(False)

                        ##Turn on laser
                        Laser[wave_str].turnOn()
            #             skyraLaser.turnOn(laser.names_to_channels[list(experiment.wavelengths)[ch]])

                        # CAPTURE IMAGES
                        count_old = 0
                        count_new = 0
                        count = 0
                        im = np.zeros((session.nFrames, camera.Y, camera.X), dtype = 'uint16') #

                        #after this loop, im.shape = (direction of X scan, direction of vertical FOV, direction of horizontal FOV) i.e. (X, Z, Y)
                        while count < session.nFrames-1:
                            timer.sleep(0.01)
                            # Get frames.
            #                 print('getting frames')
                            [frames, dims] = hcam.getFrames()
                            count_old = count
                            # Save frames.
                            for aframe in frames:
                                np_data = aframe.getData()
                                im[count] = np.reshape(np_data, (camera.Y, camera.X)) #orient so camera's vertical FOV is row direction
                                count += 1
                            count_new = count
                            
                            if count_new != 0 and count_new == count_old:
                                count = session.nFrames #reached last frame in scan
                                print('Acquired last frame')
                                
                        print(str(count_new) + '/' + str(session.nFrames) + ' frames collected...')

                        # START IMAGING LOOP
                        h5.h5write(dest,im, tile + session.zTiles*session.yTiles*ch, 0, count_new)


                        waveformGenerator.ao_task.stop()
            #             waveformGenerator.write_zeros(daq=daq)
                        # For some reason this write_zeros works but the above doesn't?
                        # laser stops and starts appropriately with this one active
                        # and the top write_zeros() commented out

            #             skyraLaser.turnOff(list(experiment.wavelengths)[ch]) ## for Skyra
                        Laser[wave_str].turnOff() #For obis laser
                        
                        # cam.stop() ## for pco camera
                        hcam.stopAcquisition() #for hamamatsu camera

                        tile_end_time = timer.time()
                        tile_time = tile_end_time - tile_start_time
                        print('Tile time: ' + str(round((tile_time/60), 3)) + " min")
                        tiles_remaining = session.nWavelengths * session.zTiles * \
                            session.yTiles - (tile * session.nWavelengths + ch + 1)

                        if tiles_remaining != 0:
                            print('Estimated time remaining: ',
                                  str(round((tile_time*tiles_remaining/3600), 3)),
                                  " hrs")

                    tile += 1

            end_time = timer.time()

            print("Total time = ",
                  str(round((end_time - start_time)/3600, 3)),
                  " hrs")

            response = xyzStage.getMotorStatus()
            while response[0] == 'B':
                response = xyzStage.getMotorStatus()

            hcam.shutdown()
            # cam.close() ## For PCO camera
            # etl.close(soft_close=True)
            # waveformGenerator.counter_task.close()
            waveformGenerator.ao_task.close()
            xyzStage.shutDown()
            # Laser.shutDown() ## For cobolt
            for ch in range(session.nWavelengths): ## For OTLS-3
                wave_str = list(experiment.wavelengths)[ch]
                Laser[wave_str].shutDown()
            fWheel.shutDown()


def write_voltages(daq,
                   laser,
                   camera,
                   experiment,
                   ch):

    print('writing voltages')
    n2c = daq.names_to_channels
    wave_key = list(experiment.wavelengths)[ch]  # wavelength as a string
    print(wave_key)

    # convert max / min / peak-to-peak (DAQExpress convention)
    # to offset / amplitude
    xoffset = (daq.xmax[wave_key] + daq.xmin[wave_key]) / 2
    xamplitude = daq.xpp[wave_key] / 2
    yoffset = (daq.ymax[wave_key] + daq.ymin[wave_key]) / 2
    yamplitude = daq.ypp[wave_key] / 2
    print(xoffset)
    print(xamplitude)
    print(yoffset)
    print(yamplitude)

    samples = int(daq.rate*camera.expTime/1e3)  # number of samples for DAQ

    line_time = 9.76/1.0e6  # seconds, constant for pco.edge camera
    roll_time = line_time*camera.Y/2.0  # chip rolling time in seconds
    roll_samples = int(np.floor(roll_time*daq.rate))  # rolling samples

    on_time = camera.expTime/1e3 - roll_time  # ON time for strobing laser
    on_samples = int(np.floor(on_time*daq.rate))  # ON samples

    galvo_time = 365/1.0e6  # galvo delay time
    galvo_samples = int(np.floor(galvo_time*daq.rate))

    buffer_time = 50/1.0e6
    buffer_samples = int(np.floor(buffer_time*daq.rate))

    voltages = np.zeros((daq.num_channels, samples))  # create voltages array

    # X Galvo scanning:
    period_samples = np.linspace(0,
                                 2 * math.pi, on_samples + 2 * buffer_samples)
    snap_back = np.linspace(xoffset + xamplitude,
                            xoffset - xamplitude,
                            samples - on_samples - 2 * buffer_samples)
    voltages[n2c['xgalvo'], :] = xoffset
    voltages[n2c['xgalvo'],
             roll_samples - galvo_samples - buffer_samples:
             roll_samples + on_samples - galvo_samples + buffer_samples] = \
        -2 * (xamplitude / math.pi) * \
        np.arctan(1.0 / (np.tan(period_samples / 2.0))) + xoffset
    voltages[n2c['xgalvo'],
             roll_samples + on_samples - galvo_samples + buffer_samples:
             samples] = \
        snap_back[0:samples - (roll_samples + on_samples - galvo_samples +
                  buffer_samples)]
    voltages[n2c['xgalvo'],
             0:roll_samples - galvo_samples - buffer_samples] = \
        snap_back[samples - (roll_samples + on_samples - galvo_samples +
                  buffer_samples):samples]

    # Y Galvo scanning:
    period_samples = np.linspace(0,
                                 2 * math.pi, on_samples + 2 * buffer_samples)
    snap_back = np.linspace(yoffset + yamplitude,
                            yoffset - yamplitude,
                            samples - on_samples - 2 * buffer_samples)
    voltages[n2c['ygalvo'], :] = yoffset
    voltages[n2c['ygalvo'],
             roll_samples - galvo_samples - buffer_samples:
             roll_samples + on_samples-galvo_samples + buffer_samples] = \
        -2 * (yamplitude / math.pi) * \
        np.arctan(1.0 / (np.tan(period_samples / 2.0))) + yoffset
    voltages[n2c['ygalvo'],
             roll_samples + on_samples - galvo_samples + buffer_samples:
             samples] = \
        snap_back[0:samples - (roll_samples + on_samples - galvo_samples +
                  buffer_samples)]
    voltages[n2c['ygalvo'],
             0:roll_samples - galvo_samples - buffer_samples] = \
        snap_back[samples - (roll_samples + on_samples - galvo_samples +
                  buffer_samples):samples]


    # # ETL scanning:
    # voltages[n2c['etl'], :] = eoffset

    # NI playing:
    # voltages[n2c['daq_active'], :] = 3.0

    # for c in range(12):
    #   plt.plot(voltages[c, :])
    #   plt.legend(loc='upper right')
    # plt.show()

    # Check final voltages for sanity
    # Assert that voltages are safe
    assert (1.0/(1.0/on_time)) <= 800.0
    assert np.max(voltages[n2c['xgalvo'], :]) <= 5.0
    assert np.min(voltages[n2c['xgalvo'], :]) >= -5.0
    assert np.max(voltages[n2c['ygalvo'], :]) <= 5.0
    assert np.min(voltages[n2c['ygalvo'], :]) >= -5.0
    # assert np.max(voltages[n2c['etl'], :]) <= 5.0
    # assert np.min(voltages[n2c['etl'], :]) >= 0.0
    # assert np.max(voltages[n2c['daq_active'], :]) <= 5.0
    # assert np.min(voltages[n2c['daq_active'], :]) >= 0.0
    # assert np.max(voltages[n2c[wave_key], :]) <= 5.0
    # assert np.min(voltages[n2c[wave_key], :]) >= 0.0

    return voltages, (camera.expTime/1e3-2*roll_time)*1000


def zero_voltages(daq, camera):
    # samples = int(daq.rate*camera.expTime/1e3)  # number of samples for DAQ
    voltages = np.zeros((daq.num_channels, 2))  # create voltages array
    return voltages


# The MIT License
#
# Copyright (c) 2020 Adam Glaser, University of Washington
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
