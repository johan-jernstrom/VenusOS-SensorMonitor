#!/usr/bin/env python
import logging
from gi.repository import GLib # type: ignore
from dbus.mainloop.glib import DBusGMainLoop # type: ignore
from cpu_temp import CPUTemp
from w1_temps import W1Temps
from ble_temps import BLETemps
from dc_currents import DcCurrents
from alarm import AlarmBuzzer
from dbus_service import DCSourceService, TemperatureService

# Create a dictionary to keep track of the services that are currently active, one for temperature services and one for current services
tempServices = {}
currentServices = {}

# Create the sensors that will be monitored and exposed to dbus
cpu_temp = CPUTemp()
w1_temps = W1Temps()
ble_temps = BLETemps()
dc_currents = DcCurrents()
alarm = AlarmBuzzer()

def update_temp_services():
    logging.debug('Updating temperature services...')
    newTemps = ble_temps.get_values() # get BLE temperatures
    newTemps.update(w1_temps.read_temperatures())   # add w1 temperatures
    newTemps['rpi'] = cpu_temp.read_temperature()   # add CPU temperature
    
    for id in newTemps:
        data = newTemps[id]
        if data is None:
            continue

        create_temp_service_if_not_exists(data)

        # get SensorData and update service
        service = tempServices[id]
        service.update(data.temperature, data.humidity, data.battery)

        # check if temperature is above the high temperature alarm
        alarm.check_value(data.temperature, service.settings['HighTempAlarm'], id)

    # disconnect services that are no longer available by checking if the id is in the newTemps dictionary
    for id in list(tempServices):
        if id not in newTemps:
            tempServices[id].disconnect()
    
    return True

def create_temp_service_if_not_exists(sensorData):
    id = sensorData.id
    if id not in tempServices:
        instance = 1000 + len(tempServices)
        tempServices[id] = TemperatureService(sensorData.connection, sensorData.id, instance)

def update_current_services():
    latestSmoothedCurrents = dc_currents.get_latest_smoothed_values()  # Get the latest smoothed values from the dc_currents instance
    for id in latestSmoothedCurrents:
        create_current_service_if_not_exist(id)
        temp = find_temp_for_current(id)
        current = latestSmoothedCurrents[id].get_value()  # Get the numeric value
        if abs(current) < 1:    # ignore small currents
            current = 0
        currentServices[id].update(current, temp)

        # Anomaly detection: trigger alarm if difference > 50% of baseline
        if currentServices[id].settings.get('DiffAlarm', 0) == 0:
            continue    # skip diff check if alarm is disabled
        baseline = latestSmoothedCurrents[id].get_baseline_current() if latestSmoothedCurrents[id].get_baseline_current() is not None else 0

        if baseline is None or baseline < 2:  # if baseline is None or too low, skip diff check
            if abs(current) > 3 :  # unless current is actually high, then trigger alarm
                alarm.check_value(100, currentServices[id].settings['DiffAlarm'], id)
            logging.debug(f"Skipping diff check for id {id} because baseline is None or too low: {baseline}")
            continue

        diffPercent = abs((current - baseline) / baseline) * 100
        alarm.check_value(diffPercent, currentServices[id].settings['DiffAlarm'], id)

    # disconnect services that are no longer available
    for id in list(currentServices):
        if id not in latestSmoothedCurrents:
            currentServices[id].disconnect()
    
    return True

def find_temp_for_current(id):
    # get name of service that has the same CustomName as the CustomName of the current service
    customName = currentServices[id].settings['CustomName']
    for tempService in tempServices.values():
        if tempService.settings['CustomName'] == customName:
            return tempService.dbusservice['/Temperature']
    return None

def create_current_service_if_not_exist(id):
    if id in currentServices:
        return
    instance = 2000 + len(currentServices)
    currentServices[id] = DCSourceService('I2C', id, instance)

def main():
    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)
    mainloop = GLib.MainLoop()

    # Start the BLE scanner
    ble_temps.start_scanner()
    logging.info('BLE scanner started, moving on')

    # make initial call
    update_temp_services()
    # and then every 5 seconds
    GLib.timeout_add_seconds(5, lambda: update_temp_services())

    # # make initial call
    update_current_services()
    # # and then every 1 seconds
    GLib.timeout_add_seconds(1, lambda: update_current_services())

    logging.info('Connected to dbus, and switching over to GLib.MainLoop() (= event based)')
    mainloop.run()
    dc_currents.shutdown()  # Ensure we stop the background thread properly
    logging.info('Exiting...')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s")
    main()