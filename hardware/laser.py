
#!/usr/bin/python

"""
LSM scanning code

# Adam Glaser 07/19
# Edited by Kevin Bishop 5/22
# Edited by Rob Serafin 9/22

"""
import hardware.skyra as skyra
import hardware.obis as obis
# import hardware.sapphire as sapphire

class laser(object):
    def __init__(self, laser_dict):

        self.models = laser_dict['laser_models']
        self.ports = laser_dict['laser_ports']
        self.rate = laser_dict['rate']
        self.names_to_channels = laser_dict['names_to_channels']
        self.max_powers = laser_dict['max_powers']
        self.system_name = laser_dict['system_name']
        self.use_LUT = laser_dict['use_LUT']
        self.min_currents = laser_dict['min_currents']
        self.max_currents = laser_dict['max_currents']
        self.strobing = laser_dict['strobing']

    def initialize(self, experiment, scan, model, port):

        if self.system_name == 'OTLS 4':
            print('initializing laser')
            print('using laser parameters use_LUT=' + str(self.use_LUT) +
                  ' system_name=' + self.system_name)
            input('If this is NOT correct, press CTRL+C to exit and avoid damage' +
                  ' to the laser. If this correct, press Enter to continue.')

            min_currents_sk_num = {}
            max_currents_sk_num = {}
            max_powers_sk_num = {}

            for ch in experiment.wavelengths:  # ch is wavelength as a string
                min_currents_sk_num[self.names_to_channels[ch]] = \
                    self.min_currents[ch]
                max_currents_sk_num[self.names_to_channels[ch]] = \
                    self.max_currents[ch]
                max_powers_sk_num[self.names_to_channels[ch]] = \
                    self.max_powers[ch]

            skyraLaser = skyra.Skyra(baudrate=self.rate,
                                     port=self.port)
            skyraLaser.setMinCurrents(min_currents_sk_num)
            skyraLaser.setMaxCurrents(max_currents_sk_num)
            skyraLaser.setMaxPowers(max_powers_sk_num)
            skyraLaser.setUseLUT(self.use_LUT)
            skyraLaser.importLUT()

            for ch in list(self.names_to_channels):
                skyraLaser.setModulationOn(self.names_to_channels[ch])
                skyraLaser.setDigitalModulation(self.names_to_channels[ch], 1)

                #  new, to ensure analog mod is not active
                skyraLaser.setAnalogModulation(self.names_to_channels[ch], 0)
            for ch in list(experiment.wavelengths):
                skyraLaser.setModulationHighCurrent(self.names_to_channels[ch],
                                                    experiment.wavelengths[ch])
                skyraLaser.turnOn(self.names_to_channels[ch])
            for ch in list(experiment.wavelengths):
                skyraLaser.setModulationLowCurrent(self.names_to_channels[ch], 0)
                highest_power = experiment.wavelengths[ch] / \
                    np.exp(-scan.zTiles * experiment.zWidth /
                           experiment.attenuations[ch])
                if skyraLaser.use_LUT:
                    maxPower = skyraLaser.LUT['ch' + str(self.names_to_channels[ch])]['power'][-1]
                else:
                    maxPower = self.max_powers[ch]
                if highest_power > maxPower:
                    raise Exception('Power will be out of range at final Z ' +
                                    'position. Adjust power or attenuation.\n')

            print('finished initializing laser')
            return skyraLaser

        if model == 'obis':

            obisLaser = obis.Obis(baudrate = self.rate, port = port)

            return obisLaser

        if model == 'sapphire':

            sapphireLaser = sapphire.SapphireLaser(com = port)   

            return sapphireLaser

