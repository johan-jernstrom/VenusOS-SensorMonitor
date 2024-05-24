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
        self.i2cInitialized = False
        self.numberOfChannels = numberOfChannels
    
    def ensure_i2c(self):
        if self.i2cInitialized:
            return
        try:
            self.logger.debug("dc_currents: Initializing I2C")
            # Initialize the I2C interface
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # Create an ADS1115 object
            ads = ADS.ADS1115(i2c, gain=2/3)

            for i in range(self.numberOfChannels):
                setattr(self, 'channel' + str(i), AnalogIn(ads, getattr(ADS, 'P' + str(i))))
                self.logger.debug("dc_currents: Channel " + str(i) + " initialized")
            self.i2cInitialized = True
        except Exception as e:
            self.logger.error("dc_currents: Error initializing I2C: " + str(e))
            self.i2cInitialized = False


    def read_currents(self):
        values = {}
        self.ensure_i2c()

        if not self.i2cInitialized:
            self.logger.warning("dc_currents: I2C not initialized")
            return values

        # Read the voltage of each channel
        for i in range(self.numberOfChannels):
            voltage = getattr(self, 'channel' + str(i)).voltage
            self.logger.debug("dc_currents: Channel " + str(i) + " voltage: " + str(voltage))   
            current = 150/5 * voltage   # 150A/5V
            values[str(i)] = round(current, 3)
            self.logger.debug("dc_currents: Channel " + str(i) + " current: " + str(current))
        return values