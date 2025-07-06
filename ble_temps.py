import asyncio
from datetime import datetime, timedelta
from bleak import BleakScanner
import logging
from threading import Thread, Lock, Event
from TempSensorData import TempSensorData

class BLETemps:
    """
    Class to scan for BTHome compatible BLE devices and read temperature and humidity values from them.

    Before using the class, the start_scanner() method should be called to start the scanner thread. The scanner thread will scan for BLE devices and read temperature and humidity values from them. The values are stored in a dictionary with the device name as the key and the temperature and humidity values as the value.
    
    The get_values() method can be called to get the latest temperature and humidity values read from the devices.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__) # create logger
        self.logger.info("Initializing BLE Temps...")

        # create dict containg device name as key and SensorData object as value
        self.values = {} # store latest values
        self.scanner_thread = None
        self.stop_event = Event()
        self.Lock = Lock()

    def _parse_bthome_v2_data(self, data):
        """
        Decodes the BTHome advertisement data byte array in the format documented at:
            https://bthome.io/format/

        Also inspired by:
            https://github.com/Bluetooth-Devices/bthome-ble/blob/V2/src/bthome_ble/parser.py
        
        Args:
            data (bytes): The byte array containing the advertisement data.
        
        Returns:
            SensorData: An instance of SensorData containing the decoded sensor data.
        """
        # ensure that the data is at least 3 bytes long
        if len(data) < 11:
            self.logger.debug(f"Data is too short: {data}")
            return None
        
        index = 0

        # skip the first 2 bytes (UUID)
        index += 2

        # skip the next byte (BTHome Device Information)
        index += 1

        # Create an instance of SensorData to store the decoded values
        sensor_data = TempSensorData()
        sensor_data.timestamp = datetime.now()
        sensor_data.connection = 'BLE'

        # Iterate through the remaining bytes to extract sensor data
        while index < len(data):
            # Extract the object ID (1 byte)
            object_id = data[index]
            index += 1
            # Decode the value based on the object ID 
            if object_id == 0x01:  # Battery
                sensor_data.battery = int.from_bytes(data[index:index+1], byteorder='little')
                index += 1
            elif object_id == 0x02:  # Temperature
                sensor_data.temperature = round(int.from_bytes(data[index:index+2] , byteorder='little', signed=True) * 0.01, 1)
                index += 2
            elif object_id == 0x03:  # Humidity
                sensor_data.humidity = round(int.from_bytes(data[index:index+2], byteorder='little') * 0.01, 1)
                index += 2
            else:
                self.logger.debug(f"Unsupported object ID: {object_id}")  # we are only interested in battery, temperature and humidity
                return None
        return sensor_data

    def start_scanner(self):
        self.logger.info("Starting BLE Temps scanner...")
        if self.scanner_thread is not None:
            self.logger.warning("Scanner thread already started. Ignoring request to start again.")
            return
        self.scanner_thread = Thread(target=self._scan,name="BLE Temp Scanner Thread", daemon=True)
        self.scanner_thread.start()

    def stop_scanner(self):
        self.logger.info("Stopping BLE Temps scanner...")
        if self.scanner_thread is None:
            self.logger.warning("BLE Temps scanner thread not started. Ignoring request to stop.")
            return
        self.stop_event.set()   # signal thread to stop
        self.scanner_thread.join()  # wait for thread to stop
        self.scanner_thread = None  # reset thread

    def _scan(self):
        asyncio.run(self._scanAsync())

    async def _scanAsync(self):
        try:
            async with BleakScanner(self._scan_callback) as scanner:
                self.logger.info('Starting scan...')
                while not self.stop_event.is_set():
                    await asyncio.sleep(1)
                await self.stop_event.wait()    # wait for stop event
        except Exception as e:
            self.logger.exception("Error during scan")
        self.logger.info("Scanning stopped.")

    def _scan_callback(self, device, advertising_data):
        # logging.debug(f"Device {device.name} ({device.address}) RSSI: {device.rssi}")
        if not device.address.startswith("A4:C1:38:"): # All Xiaomi Mijia LYWSD03MMC devices start with this address
            return
        self.logger.debug(f"Found Xiaomi Mijia device {device.name} ({device.address}) RSSI: {advertising_data.rssi}")
        advertisement_data = advertising_data.service_data.get('0000fcd2-0000-1000-8000-00805f9b34fb')  # BTHome V2 service UUID
        if not advertisement_data:
            self.logger.warning(f"No BTHome V2 service data found in advertisement data for device {device.name}")
            return
        self.logger.debug(f"BTHome V2 service found in advertisement data")

        sensor_data = self._parse_bthome_v2_data(advertisement_data)
        if not sensor_data:
            self.logger.debug(f"Failed to parse sensor data for device {device.name}")
            return
        sensor_data.id = device.name
        self.logger.debug(f"Device {device.name} has temperature {sensor_data.temperature} and humidity {sensor_data.humidity} at {sensor_data.timestamp}")
        with self.Lock:
            self.values[device.name] = sensor_data

    def get_values(self):
        with self.Lock:
            # remove values older than 5 minutes before returning
            self.values = {k:v for k,v in self.values.items() if v is not None and v.timestamp > datetime.now() - timedelta(minutes=5)}
            return self.values