import datetime
import board
import busio
# https://docs.circuitpython.org/projects/ads1x15/en/latest/index.html
import adafruit_ads1x15.ads1115 as ADS # type: ignore
from adafruit_ads1x15.analog_in import AnalogIn # type: ignore
import logging
import CSVLogger  # Assuming you have a CSVLogger class for logging to CSV

class SmoothedValue:
    def __init__(self, initial_value=0, window_size=5):
        self.buffer = [initial_value] * window_size
    
    def update(self, value):
        self.buffer.pop(0)
        self.buffer.append(value)
        return sum(self.buffer) / len(self.buffer)

class DcCurrents:
    def __init__(self, channels = [1,2,3], amp_per_voltage = 150 / 5):
        """
        Initializes the DcCurrents class to read DC currents from specified channels.

        Args:
            channels (list): List of channels to read from. Default is [1, 2, 3]. Channel 0 is not used in current wiring
            amp_per_voltage (float): Conversion factor from voltage to current. Default is 150A/5V.
        """
        self.logger = logging.getLogger(__name__)
        self.csvLogger = CSVLogger.CSVLogger('logs', 'dc_currents_log_' + datetime.now().strftime("%Y%m%d") + '.csv', flush_interval=60)  # Log every minute
        self.logger.info("dc_currents: Initializing")
        self.amp_per_voltage = amp_per_voltage
        self.i2cConnected = False
        self.channels = channels
        self.smoothed_values = {str(i): SmoothedValue() for i in self.channels}
        # for i in self.channels:
        #     setattr(self, 'channel' + str(i) + 'Zero', 0)   # initialize zero values
    
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

    # def set_zero(self):
    #     self.ensure_i2c_connected()
    #     if not self.i2cConnected:
    #         return
    #     try:
    #         for i in self.channels:
    #             voltage = getattr(self, 'channel' + str(i)).voltage
    #             setattr(self, 'channel' + str(i) + 'Zero', voltage)
    #             self.logger.debug("dc_currents: Channel " + str(i) + " zero set to " + str(voltage))
    #     except Exception as e:
    #         self.i2cConnected = False
    #         self.logger.debug("dc_currents: Error setting zero: " + str(e))

    def read_currents(self):
        values = {}
        raw_voltages = {}
        raw_currents = {}

        current = 0 # TODO: Read from DBUS
        ad_voltage = 0 # TODO: Read from DBUS

        self.ensure_i2c_connected()
        if not self.i2cConnected:
            self.logger.debug("dc_currents: I2C not initialized")
            for i in self.channels:
                values[str(i)] = -999
            return values
        
        # Read the voltage of each channel
        for i in self.channels:
            try:
                ad_voltage = getattr(self, 'channel' + str(i)).voltage
                # ad_voltage -= getattr(self, 'channel' + str(i) + 'Zero')
                current = ad_voltage * self.amp_per_voltage
                raw_voltages[i] = ad_voltage
                raw_currents[i] = current
                values[str(i)] = self.smoothed_values[str(i)].update(current)
                
            except Exception as e:
                self.i2cConnected = False
                self.logger.error(f"dc_currents: Error reading channel {i}: {e}")
                values[str(i)] = -999
        # Log the values to CSV
        if self.csvLogger:
            self.csvLogger.log(current, ad_voltage,
                               raw_voltages.get(1, -999), raw_currents.get(1, -999), values.get('1', -999),
                               raw_voltages.get(2, -999), raw_currents.get(2, -999), values.get('2', -999),
                               raw_voltages.get(3, -999), raw_currents.get(3, -999), values.get('3', -999))
        
        # Return the smoothed values
        return values

    def __del__(self):
        if self.csvLogger:
            self.csvLogger.flush()
            self.logger.info("dc_currents: CSV logger flushed")
