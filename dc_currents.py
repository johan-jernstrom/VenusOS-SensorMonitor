import board
import busio
# https://docs.circuitpython.org/projects/ads1x15/en/latest/index.html
import adafruit_ads1x15.ads1115 as ADS # type: ignore
from adafruit_ads1x15.analog_in import AnalogIn # type: ignore
import logging

class DcCurrents:
    def __init__(self, channels = [1,2,3]):
        self.logger = logging.getLogger(__name__)
        self.logger.info("dc_currents: Initializing")
        self.i2cConnected = False
        self.channels = channels    # Channels to read from. Channel 0 is not used in current wiring
    
    def ensure_i2c_connected(self):
        if self.i2cConnected:
            return
        try:
            self.logger.debug("dc_currents: Initializing I2C")
            # Initialize the I2C interface
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # Create an ADS1115 object
            ads = ADS.ADS1115(i2c, gain=2/3)

            for i in self.channels:
                setattr(self, 'channel' + str(i), AnalogIn(ads, getattr(ADS, 'P' + str(i))))
                self.logger.debug("dc_currents: Channel " + str(i) + " initialized")

            self.i2cConnected = True
        except Exception as e:
            self.logger.debug("dc_currents: Error initializing I2C: " + str(e))
            self.i2cConnected = False

    def set_zero(self):
        self.ensure_i2c_connected()
        if not self.i2cConnected:
            return
        try:
            for i in self.channels:
                voltage = getattr(self, 'channel' + str(i)).voltage
                self.logger.debug("dc_currents: Channel " + str(i) + " voltage: " + str(voltage))
                setattr(self, 'channel' + str(i) + 'Zero', voltage)
        except Exception as e:
            self.i2cConnected = False
            self.logger.debug("dc_currents: Error setting zero: " + str(e))

    def read_currents(self):
        values = {}
        self.ensure_i2c_connected()
        try:
            if not self.i2cConnected:
                self.logger.debug("dc_currents: I2C not initialized")
                return values

            # Read the voltage of each channel
            for i in self.channels:
                voltage = getattr(self, 'channel' + str(i)).voltage
                self.logger.debug("dc_currents: Channel " + str(i) + " voltage: " + str(voltage))
                voltage -= getattr(self, 'channel' + str(i) + 'Zero')
                self.logger.debug("dc_currents: Channel " + str(i) + " voltage after zero: " + str(voltage))
                current = 150/5 * voltage   # 150A/5V
                values[str(i)] = round(current, 1)
                self.logger.debug("dc_currents: Channel " + str(i) + " current: " + str(current))
        except Exception as e:
            self.i2cConnected = False
            self.logger.debug("dc_currents: Error reading currents: " + str(e))
        return values