import os
import logging
from TempSensorData import TempSensorData

class CPUTemp:
    def __init__(self):
        self.logger = logging.getLogger(__name__) # create logger

    def read_temperature(self):
        """
        Read the CPU temperature from the Raspberry Pi.
        The temperature is read from the file /sys/devices/virtual/thermal/thermal_zone0/temp.
        The value is divided by 1000 to get the temperature in degrees Celsius.
    
        Returns:
            SensorData: An instance of SensorData containing the CPU temperature

        """
        if not os.path.exists('/sys/devices/virtual/thermal/thermal_zone0/temp'):
            self.logger.error("CPU temperature not found")
            return None
    
        fd  = open('/sys/devices/virtual/thermal/thermal_zone0/temp','r')
        value = float(fd.read())
        value = round(value / 1000.0, 1)
        self.logger.debug("CPU Temperature: " + str(value))
        fd.close
        sensor_data = TempSensorData(id='rpi', connection='CPU', temperature=value)
        return sensor_data
    