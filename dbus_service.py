import logging
import sys
import os
import traceback
import dbus # type: ignore
# import victron package for updating dbus (using lib from built in service)
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-modem'))
from vedbus import VeDbusService # type: ignore
from settingsdevice import SettingsDevice # type: ignore

VOLTAGE_TEXT = lambda path,value: "{:.2f}V".format(value)
CURRENT_TEXT = lambda path,value: "{:.0f}A".format(value)
POWER_TEXT = lambda path,value: "{:.2f}W".format(value)
ENERGY_TEXT = lambda path,value: "{:.6f}kWh".format(value)
TEMPERATURE_TEXT = lambda path,value: "{:.2f}'C".format(value)

class SystemBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SYSTEM)

class SessionBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SESSION)

class DbusService:
    def __init__(self, type, connection, id, deviceInstance):
        self.logger = logging.getLogger(__name__) # create logger
        self.type = type
        self.name = f'{connection}_{id}'
        self.servicename = f'com.victronenergy.{type}.{self.name}'
        self.dbusservice = VeDbusService(self.servicename, self.dbusconnection())

        # Create the management objects, as specified in the ccgx dbus-api document
        self.dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self.dbusservice.add_path('/Mgmt/ProcessVersion', '1.0')
        self.dbusservice.add_path('/Mgmt/Connection', connection)

        # Create the mandatory objects
        self.dbusservice.add_path('/DeviceInstance', deviceInstance)
        self.dbusservice.add_path('/ProductId', 0)
        self.dbusservice.add_path('/ProductName', 'Sensor Monitor')
        self.dbusservice.add_path('/FirmwareVersion', 1.0)
        self.dbusservice.add_path('/HardwareVersion', 1.0)
        self.dbusservice.add_path('/Connected', 1)
        self.supportedSettings = {}
        self.settings = None

        self.logger.info(f"Service created {self.servicename}")


    def _init_settings(self, settingList):
        """
        Add settings to the device.

        Args:
            settingList (list): A list of tuples containing the setting name and its corresponding values (default, min, max).

        Returns:
            None
        """
        settingsBasePath = f"/Settings/{self.type.capitalize()}/{self.name}"

        for settingName, values in settingList:
            self.supportedSettings[settingName] = [settingsBasePath + '/' + settingName, values[0], values[1], values[2]]
            self.logger.debug(f"Added setting {settingName} with values {values}")
        self.settings = SettingsDevice(bus=self.dbusconnection(), supportedSettings=self.supportedSettings, eventCallback=self._handle_setting_changed)

        self.logger.info(f"Settings added to service {self.servicename}")

        # set values of paths to value found in settings
        for settingName, values in settingList:
            value = self.settings[settingName]
            self.logger.debug(f"Setting {settingName} to {self.settings[settingName]}")
            self.dbusservice['/' + settingName] = value

    def _handle_value_changed(self, path, value):
        self.logger.info(f"Updated value of {path} to {value}")
        try:
            if self.settings is not None:
                setting_name = path.replace('/', '')
                self.settings[setting_name] = value
                self.logger.debug(f"Updated setting {setting_name} to {value}")  
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"Failed to update setting {path} to {value}: {e}")
        return True # accept the change
    
    def _handle_setting_changed(self, setting, old, new):
        self.logger.info(f"Setting {setting} changed from {old} to {new}")
        return True # accept the change
    
    def dbusconnection(self):
        return SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else SystemBus()
    
    def disconnect(self):
        self.logger.info(f"Disconnecting service {self.servicename}")
        self.dbusservice['/Connected'] = 0

    def update(self):
        if(self.dbusservice['/Connected'] == 0):
            self.dbusservice['/Connected'] = 1
            self.logger.info(f"Reconnecting service {self.servicename}")
    
class TemparatureService(DbusService):
    def __init__(self, connection, id, deviceInstance):
        super().__init__('temperature', connection, id, deviceInstance)

        self.dbusservice.add_path('/Temperature', None, gettextcallback=TEMPERATURE_TEXT)
        self.dbusservice.add_path('/TemperatureType', 0, writeable=True, onchangecallback = self._handle_value_changed)
        self.dbusservice.add_path('/CustomName', None, writeable=True, onchangecallback = self._handle_value_changed)
        self.dbusservice.add_path('/HighTempAlarm', 0, writeable=True, gettextcallback=TEMPERATURE_TEXT, onchangecallback = self._handle_value_changed)

        self._init_settings([('TemperatureType', [0, 0, 2]), ('CustomName', [self.name, 0, 0]), ('HighTempAlarm', [70, 0, 100])])

    def update(self, tempValue, humidityValue = None):
        super().update()
        self.dbusservice['/Temperature'] = tempValue
        self.logger.debug(f"Updated temperature to {tempValue}")
        if humidityValue is not None:
            self.dbusservice['/Humidity'] = humidityValue
            self.logger.debug(f"Updated humidity to {humidityValue}")

    def disconnect(self):
        self.dbusservice['/Temperature'] = None
        super().disconnect()
    
class DCSourceService(DbusService):
    def __init__(self, connection, id, deviceInstance):
        super().__init__('dcsource', connection, id, deviceInstance)
        self.dbusservice.add_path('/CustomName', None, writeable=True, onchangecallback = self._handle_value_changed)

        # self._dbusservice.add_path("/Dc/0/Voltage", None, gettextcallback=VOLTAGE_TEXT)
        self.dbusservice.add_path("/Dc/0/Current", None, gettextcallback=CURRENT_TEXT)
        self.dbusservice.add_path("/Dc/0/Temperature", None, gettextcallback=TEMPERATURE_TEXT)
        # self._dbusservice.add_path("/Dc/0/Power", None, gettextcallback=POWER_TEXT)
        # self._dbusservice.add_path("/Alarms/LowVoltage", 0)
        # self._dbusservice.add_path("/Alarms/HighVoltage", 0)
        self.dbusservice.add_path("/Alarms/LowTemperature", 0, writeable=True, onchangecallback = self._handle_value_changed)
        self.dbusservice.add_path("/Alarms/HighTemperature", 0, writeable=True, onchangecallback = self._handle_value_changed)
        # self._dbusservice.add_path("/History/MaximumVoltage", 0, gettextcallback=VOLTAGE_TEXT)
        self.dbusservice.add_path("/History/MaximumCurrent", 0, gettextcallback=CURRENT_TEXT)
        # self._dbusservice.add_path("/History/MaximumPower", 0, gettextcallback=POWER_TEXT)
        self.dbusservice.add_path('/DiffAlarm', 50, writeable=True, onchangecallback=self._handle_value_changed)

        self._init_settings([('CustomName', [self.name, 0, 0]), ('Alarms/LowTemperature', [0, -20, 100]), ('Alarms/HighTemperature', [0, -20, 100]), ('DiffAlarm', [50, 0, 100])])
        
    def update(self, current, temperature):
        super().update()
        self.dbusservice['/Dc/0/Current'] = current
        self.dbusservice['/Dc/0/Temperature'] = temperature
        if self.dbusservice['/History/MaximumCurrent'] < current:
            self.dbusservice['/History/MaximumCurrent'] = current
            self.logger.debug(f"Updated maximum current to {current}")
        
        self.logger.debug(f"Updated current to {current} and temperature to {temperature}")

    def disconnect(self):
        self.dbusservice['/Dc/0/Current'] = None
        self.dbusservice['/Dc/0/Temperature'] = None
        super().disconnect()
