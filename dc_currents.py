import random
import board
import busio
# https://docs.circuitpython.org/projects/ads1x15/en/latest/index.html
import adafruit_ads1x15.ads1115 as ADS # type: ignore
from adafruit_ads1x15.analog_in import AnalogIn # type: ignore
import logging

class DcCurrents:
    def __init__(self, numberOfChannels = 3):
        self.logger = logging.getLogger(__name__)
        self.logger.info("dc_currents: Initializing")

        self.numberOfChannels = numberOfChannels
 
        # # Initialize the I2C interface
        # i2c = busio.I2C(board.SCL, board.SDA)
        
        # # Create an ADS1115 object
        # ads = ADS.ADS1115(i2c, gain=2/3)

        # for i in range(numberOfChannels):
        #     setattr(self, 'channel' + str(i), AnalogIn(ads, getattr(ADS, 'P' + str(i))))
        #     self.logger.debug("dc_currents: Channel " + str(i) + " initialized")

    def read_currents(self):
        values = {}

        # Read the voltage of each channel
        for i in range(self.numberOfChannels):
            voltage = getattr(self, 'channel' + str(i)).voltage
            values[str(i)] = round(voltage, 3)
            self.logger.debug("dc_currents: Channel " + str(i) + " voltage: " + str(voltage))

        return values
    
    def read_fake_random_currents(self):
        values = {}
        for i in range(self.numberOfChannels):
            values[str(i)] = round(random.uniform(0, 5), 3)
        return values