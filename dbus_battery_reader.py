import os
import sys
import dbus
# import victron package for updating dbus (using lib from built in service)
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-modem'))
from vedbus import VeDbusItemImport

# Connect to the sessionbus. Note that on ccgx we use systembus instead.
dbusConn = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()

class DbusBatteryReader:
    def __init__(self, service_name="com.victronenergy.battery.ttyUSB1"):
        self.service_name = service_name
        dbusConn = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()

        self.voltage_item = VeDbusItemImport(
            bus=dbusConn,
            serviceName=self.service_name,
            path="/Dc/0/Voltage",
            eventCallback=None,
            createsignal=False
        )
        self.current_item = VeDbusItemImport(
            bus=dbusConn,
            serviceName=self.service_name,
            path="/Dc/0/Current",
            eventCallback=None,
            createsignal=False
        )

    def get_batt_voltage_current(self):
        voltage = self.voltage_item.get_value()
        current = self.current_item.get_value()
        return float(voltage), float(current)
