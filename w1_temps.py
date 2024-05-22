import os
import logging

class W1Temps:
    def __init__(self):
        self.logger = logging.getLogger(__name__) # create logger

    def read_temperatures(self):
        values = {}
        #read list of slaves
        if not os.path.isfile('/sys/devices/w1_bus_master1/w1_master_slaves'):
            return values
        fd = open('/sys/devices/w1_bus_master1/w1_master_slaves','r')
        w1Slaves = fd.read().splitlines()
        fd.close

        if w1Slaves[0] == 'not found.':
            return values
        
        #Loop through all connected 1Wire devices, create dbusService if necessary
        for id in w1Slaves: 
            familyID = id[0:2]
            deviceID = id[3:]
            
            #DS18B20 Temp Sensors
            if familyID != '28':
                self.logger.debug("1Wire Sensor " + id + " is not a DS18B20 Temp Sensor")
                continue
            values[deviceID] = None
            #read Temp value
            if os.path.exists('/sys/devices/w1_bus_master1/'+ id +'/temperature'):
                fd  = open('/sys/devices/w1_bus_master1/'+ id +'/temperature','r')
                lines = fd.read().splitlines()
                if lines: 
                    self.logger.debug("RawValue ID" + id + ":" + lines[0])
                    if lines[0].strip('-').isnumeric():
                        value = float(lines[0])
                        value = round(value / 1000.0, 1)
                        values[deviceID] = value
                fd.close
            self.logger.debug("1Wire Sensor " + id + " Temperature: " + str(value))
        return values
        