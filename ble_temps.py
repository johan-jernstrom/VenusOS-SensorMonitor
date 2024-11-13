import asyncio
from datetime import datetime, timedelta
from bleak import BleakScanner
import logging
from threading import Thread, Lock
from SensorData import SensorData

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
        self.stop_event = asyncio.Event()
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
            logging.debug(f"Data is too short: {data}")
            return None
        
        index = 0

        # skip the first 2 bytes (UUID)
        index += 2

        # skip the next byte (BTHome Device Information)
        index += 1

        # Create an instance of SensorData to store the decoded values
        sensor_data = SensorData()

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
            self.logger.warn("Scanner thread already started. Ignoring request to start again.")
            return
        self.scanner_thread = Thread(target=self._scan,name="BLE Temp Scanner Thread", daemon=True)
        self.scanner_thread.start()

    def stop_scanner(self):
        self.logger.info("Stopping BLE Temps scanner...")
        if self.scanner_thread is None:
            self.logger.warn("BLE Temps scanner thread not started. Ignoring request to stop.")
            return
        self.stop_event.set()   # signal thread to stop
        self.scanner_thread.join()  # wait for thread to stop
        self.scanner_thread = None  # reset thread

    def _scan(self):
        asyncio.run(self._scanAsync())

    async def _scanAsync(self):
        try:
            async with BleakScanner(self._scan_callback):
                logging.info('Starting scan...')
                await self.stop_event.wait()    # wait for stop event
        except Exception as e:
            self.logger.error("Error during scan: %s", e)
        self.logger.info("Scanning stopped.")

    def _scan_callback(self, device, advertising_data):
        if(device.address.startswith("A4:C1:38:")): # All Xiaomi Mijia LYWSD03MMC devices start with this address
            advertisement_data = advertising_data.service_data['0000fcd2-0000-1000-8000-00805f9b34fb']  # BTHome V2 service UUID
            if not advertisement_data:
                return
            sensor_data = self._parse_bthome_v2_data(advertisement_data)
            if sensor_data:
                self.logger.info(f"Device {device.name} Temperature: {sensor_data.temperature}°C, Humidity: {sensor_data.humidity}%, Battery: {sensor_data.battery}%")
                with self.Lock:
                    self.values[device.name] = sensor_data
        pass

    def get_values(self):
        with self.Lock:
            # remove values older than 5 minutes before returning
            self.values = {k:v for k,v in self.values.items() if v.timestamp > datetime.now() - timedelta(minutes=5)}
            return self.values

        