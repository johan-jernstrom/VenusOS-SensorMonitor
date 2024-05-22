import os
import logging

class CPUTemp:
    def __init__(self):
        self.logger = logging.getLogger(__name__) # create logger

    def read_temperature(self):
        if not os.path.exists('/sys/devices/virtual/thermal/thermal_zone0/temp'):
            self.logger.error("CPU temperature not found")
            return None
    
        fd  = open('/sys/devices/virtual/thermal/thermal_zone0/temp','r')
        value = float(fd.read())
        fd.close
        value = round(value / 1000.0, 1)
        self.logger.debug("CPU Temperature: " + str(value))
        return value
    