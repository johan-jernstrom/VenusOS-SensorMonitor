from SmoothedCurrent import SmoothedCurrent
import copy
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

class DcCurrents:
    DEFAULT_CHANNELS = [1, 2, 3] # Channels 0 is not used in current wiring
    DEFAULT_AMP_PER_VOLTAGE = 22  # theoretically 150A/5V=30A/V, but we use 22A/V since it turns out to be more accurate in practice
    DEFAULT_LOG_PATH = '/data/VenusOS-SensorMonitor/logs/dc_currents'
    DEFAULT_FLUSH_INTERVAL = 60  # seconds
    DEFAULT_SMOOTHED_WINDOW = 10  # Default window size for SmoothedValue
    DEFAULT_OFFSETS = {1: 1.453, 2: -0.847, 3: 0.008}  # Default offsets (in Amps) for each channel
    I2C_RETRY_LIMIT = 10
    ERROR_VALUE = -999

    def __init__(self, 
                 channels: list = None, 
                 amp_per_voltage: float = None, 
                 log_abs_path: str = None, 
                 flush_interval: int = None,
                 smoothed_window: int = None,
                 offsets: dict = None):
        """
        Initializes the DcCurrents class to read DC currents from specified channels.

        Args:
            channels (list): List of channels to read from. Default is [1, 2, 3]. Channel 0 is not used in current wiring
            amp_per_voltage (float): Conversion factor from voltage to current. Default is 22 from practical calibration.
            log_abs_path (str): Path for CSV logs. Default is '/data/VenusOS-SensorMonitor/logs/dc_currents'.
            flush_interval (int): CSV log flush interval in seconds. Default is 60.
            smoothed_window (int): Window size for SmoothedValue. Default is 10.
            offsets (dict): Per-channel offsets to be applied to currents. Default is {1: +1.453, 2: -0.847, 3: +0.008} from practical calibration.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing")
        self.channels = channels if channels is not None else self.DEFAULT_CHANNELS
        self.amp_per_ad_voltage = amp_per_voltage if amp_per_voltage is not None else self.DEFAULT_AMP_PER_VOLTAGE
        log_abs_path = log_abs_path if log_abs_path is not None else self.DEFAULT_LOG_PATH
        flush_interval = flush_interval if flush_interval is not None else self.DEFAULT_FLUSH_INTERVAL
        smoothed_window = smoothed_window if smoothed_window is not None else self.DEFAULT_SMOOTHED_WINDOW
        self.offsets = offsets if offsets is not None else self.DEFAULT_OFFSETS.copy()
        self.csvLogger = CSVLogger.CSVLogger(log_abs_path, flush_interval=flush_interval)
        self.i2cConnected = False
        self.smoothed_values = {str(i): SmoothedCurrent(window_size=smoothed_window) for i in self.channels}
        self.batt_reader = DbusBatteryReader()
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self._bg_thread = threading.Thread(target=self._background_reader, daemon=True)

    def start_background_thread(self):
        """
        Starts the background thread to read currents.
        This method should be called after initializing the DcCurrents instance.
        """
        if not self._bg_thread.is_alive():
            self._bg_thread.start()
            self.logger.info("Background thread started")
        else:
            self.logger.warning("Background thread is already running")

    def ensure_i2c_connected(self):
        if hasattr(self, '_i2c_fail_count'):
            pass
        else:
            self._i2c_fail_count = 0
        if self.i2cConnected:
            return
        if self._i2c_fail_count >= self.I2C_RETRY_LIMIT:
            self.logger.error("I2C initialization failed too many times (" + str(self._i2c_fail_count) + "), stopping background thread.")
            self.shutdown()  # Clean up resources
            return
        try:
            self.logger.debug("Initializing I2C")
            # Initialize the I2C interface
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # Create an ADS1115 object
            ads = ADS.ADS1115(i2c, gain=2/3)

            for i in self.channels:
                setattr(self, 'channel' + str(i), AnalogIn(ads, getattr(ADS, 'P' + str(i))))
                self.logger.debug("Channel " + str(i) + " initialized")

            self.i2cConnected = True
            self._i2c_fail_count = 0  # Reset on success
        except Exception as e:
            self.logger.exception("Error initializing I2C")
            self.i2cConnected = False
            self._i2c_fail_count += 1
            if self._i2c_fail_count > 1:
                self.logger.warning(f"I2C initialization failed {self._i2c_fail_count} times.")
            time.sleep(1)  # Delay before next retry

    def read_currents(self):
        ads_voltages = {}
        raw_currents = {}

        # Read voltage and current from dbus
        try:
            batt_voltage, batt_current = self.batt_reader.get_batt_voltage_current()
        except Exception as e:
            self.logger.exception("Error reading battery voltage and current from dbus")
            raise
        
        if(batt_current is None or abs(batt_current) < 1):
            self.logger.debug("Battery current is None or less than 1, skipping current reading")
            # Update smoothed values with None
            for i in self.channels:
                self.smoothed_values[str(i)].update(None, 0, batt_voltage)
            return
        
        # Set baseline current as battery current divided by number of channels
        baseline = batt_current / len(self.channels) if len(self.channels) > 0 else batt_current
        
        self.ensure_i2c_connected()
        if not self.i2cConnected:
            self.logger.debug("I2C not initialized, waiting 1 second before retrying")
            for i in self.channels:
                self.smoothed_values[str(i)].update(None, baseline, batt_voltage)
            # sleep to avoid busy-waiting
            time.sleep(1)
            return
        
        for i in self.channels:
            try:
                ads_voltage = getattr(self, 'channel' + str(i)).voltage
                ads_voltages[i] = ads_voltage
                current = ads_voltage * self.amp_per_ad_voltage
                offset = self.offsets.get(i, 0.0)
                current_with_offset = current + offset
                raw_currents[i] = current_with_offset
                self.smoothed_values[str(i)].update(current_with_offset, baseline, batt_voltage)
            except Exception as e:
                self.i2cConnected = False
                # self.logger.exception(f"Error reading channel {i}")
                self.logger.debug(f"Error reading channel {i}, setting smoothed value to None") # happens often, so just log it as debug
                self.smoothed_values[str(i)].update(None, baseline, batt_voltage)
        
        # Log the battery voltage and current
        # self.logger.debug(f"Battery Voltage: {batt_voltage} V, "
        #                  f"Battery Current: {batt_current} A, "
        #                  f"Channel 1 Smoothed Current: {self.smoothed_values.get('1', SmoothedCurrent()).get_value(self.ERROR_VALUE)} A ({self.smoothed_values.get('1', SmoothedCurrent()).get_quality()} %), "
        #                  f"Channel 2 Smoothed Current: {self.smoothed_values.get('2', SmoothedCurrent()).get_value(self.ERROR_VALUE)} A ({self.smoothed_values.get('2', SmoothedCurrent()).get_quality()} %), "
        #                  f"Channel 3 Smoothed Current: {self.smoothed_values.get('3', SmoothedCurrent()).get_value(self.ERROR_VALUE)} A ({self.smoothed_values.get('3', SmoothedCurrent()).get_quality()} %)")

        # Log the values to CSV if the battery current is significant
        self.csvLogger.log(batt_current, batt_voltage,
                            ads_voltages.get(1, self.ERROR_VALUE), raw_currents.get(1, self.ERROR_VALUE), self.smoothed_values.get('1', SmoothedCurrent()).get_value(self.ERROR_VALUE),
                            ads_voltages.get(2, self.ERROR_VALUE), raw_currents.get(2, self.ERROR_VALUE), self.smoothed_values.get('2', SmoothedCurrent()).get_value(self.ERROR_VALUE),
                            ads_voltages.get(3, self.ERROR_VALUE), raw_currents.get(3, self.ERROR_VALUE), self.smoothed_values.get('3', SmoothedCurrent()).get_value(self.ERROR_VALUE))

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
        Thread-safe method to retrieve the latest smoothed current.
        """
        with self.lock:
            return copy.deepcopy(self.smoothed_values)

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
            self.logger.info("CSV logger flushed")
