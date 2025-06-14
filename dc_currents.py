import datetime
import board
import busio
# https://docs.circuitpython.org/projects/ads1x15/en/latest/index.html
import adafruit_ads1x15.ads1115 as ADS # type: ignore
from adafruit_ads1x15.analog_in import AnalogIn # type: ignore
import logging
import CSVLogger  # Assuming you have a CSVLogger class for logging to CSV
from dbus_battery_reader import DbusBatteryReader
import threading
import time

class SmoothedValue:
    def __init__(self, initial_value=0, window_size=10):
        self.buffer = [initial_value] * window_size
    
    def update(self, value):
        self.buffer.pop(0)
        self.buffer.append(value)

    def set(self, value):
        """Sets the current value and updates the buffer."""
        self.buffer = [value] * len(self.buffer)

    def get(self, default=None):
        """Returns the average of the values in the buffer.
        This is a simple moving average.
        """
        if not self.buffer:
            return default
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
        self.csvLogger = CSVLogger.CSVLogger('currentlogs', flush_interval=60)  # Log every minute
        self.logger.info("dc_currents: Initializing")
        self.amp_per_ad_voltage = amp_per_voltage
        self.i2cConnected = False
        self.channels = channels
        self.smoothed_values = {str(i): SmoothedValue() for i in self.channels}
        self.batt_reader = DbusBatteryReader()
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self._bg_thread = threading.Thread(target=self._background_reader, daemon=True)
        self._bg_thread.start()
    
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
                self.logger.info("dc_currents: Channel " + str(i) + " initialized")

            self.i2cConnected = True
        except Exception as e:
            self.logger.exception("dc_currents: Error initializing I2C")
            self.i2cConnected = False

    def read_currents(self):
        ads_voltages = {}
        raw_currents = {}

        # Read voltage and current from dbus
        try:
            batt_voltage, batt_current = self.batt_reader.get_batt_voltage_current()
        except Exception as e:
            self.logger.exception("dc_currents: Error reading from dbus")
            batt_voltage = 0
            batt_current = 0

        self.ensure_i2c_connected()
        if not self.i2cConnected:
            self.logger.debug("dc_currents: I2C not initialized")
            for i in self.channels:
                self.smoothed_values[str(i)].set(-999)
            return self.smoothed_values
        
        # Read the voltage of each channel
        for i in self.channels:
            try:
                ads_voltage = getattr(self, 'channel' + str(i)).voltage
                ads_voltages[i] = ads_voltage
                current = ads_voltage * self.amp_per_ad_voltage
                raw_currents[i] = current
                self.smoothed_values[str(i)].update(current)
                
            except Exception as e:
                self.i2cConnected = False
                self.logger.exception(f"dc_currents: Error reading channel {i}")
                self.smoothed_values[str(i)].set(-999)

        # Log the values to CSV
        if self.csvLogger:
            self.csvLogger.log(batt_current, batt_voltage,
                               ads_voltages.get(1, -999), raw_currents.get(1, -999), self.smoothed_values.get('1', SmoothedValue()).get(-999),
                               ads_voltages.get(2, -999), raw_currents.get(2, -999), self.smoothed_values.get('2', SmoothedValue()).get(-999),
                               ads_voltages.get(3, -999), raw_currents.get(3, -999), self.smoothed_values.get('3', SmoothedValue()).get(-999))
        
        # Return the smoothed values
        return self.smoothed_values

    def _background_reader(self):
        while not self._stop_event.is_set():
            self._read_and_update_smoothed()
            time.sleep(0.1)  # 100 ms

    def _read_and_update_smoothed(self):
        # This method is called from the background thread
        with self.lock:
            self.read_currents()

    def get_latest_smoothed_values(self):
        """
        Thread-safe method to retrieve the latest smoothed values.
        Returns a dict of channel:str -> smoothed_value:float
        """
        with self.lock:
            return {k: v.get() for k, v in self.smoothed_values.items()}

    def stop_background_thread(self):
        self._stop_event.set()
        if self._bg_thread.is_alive():
            self._bg_thread.join()

    def shutdown(self):
        """
        Cleanly stop the background thread and flush the CSV logger.
        Call this method explicitly when you are done with the DcCurrents instance.
        """
        self.stop_background_thread()
        if self.csvLogger:
            self.csvLogger.flush()
            self.logger.info("dc_currents: CSV logger flushed")
