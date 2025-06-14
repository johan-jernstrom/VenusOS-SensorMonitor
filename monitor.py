#!/usr/bin/env python
import logging
from gi.repository import GLib # type: ignore
from dbus.mainloop.glib import DBusGMainLoop # type: ignore
from cpu_temp import CPUTemp
from w1_temps import W1Temps
from ble_temps import BLETemps
from dc_currents import DcCurrents
from alarm import AlarmBuzzer
from dbus_service import DCSourceService, TemparatureService
from TempSensorData import TempSensorData

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
    for id in tempServices:
        if id not in newTemps:
            tempServices[id].disconnect()
    
    return True

def create_temp_service_if_not_exists(sensorData):
    id = sensorData.id
    if id not in tempServices:
        instance = 1000 + len(tempServices)
        tempServices[id] = TemparatureService(sensorData.connection, sensorData.id, instance)

def update_current_services():
    newCurrents = dc_currents.read_currents()
    for id in newCurrents:
        create_current_service_if_not_exist(id)
        temp = find_temp_for_current(id)
        current = newCurrents[id]
        if current < 1 and current > -1:    # ignore small currents
            current = 0
        currentServices[id].update(current, temp)
        if currentServices[id].settings['DiffAlarm'] == 0:
            continue    # skip diff check if alarm is disabled
        if abs(sum(newCurrents.values())) / len(newCurrents) < 2:
            continue    # skip diff check if overall current is low
        diffPercent = calculate_diff(newCurrents, id, current)
        alarm.check_value(diffPercent, currentServices[id].settings['DiffAlarm'], id)

    # disconnect services that are no longer available
    for id in currentServices:
        if id not in newCurrents:
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

def calculate_diff(newCurrents, id, current):
    otherCurrents = [newCurrents[x] for x in newCurrents if x != id]
    avgOtherCurrents = sum(otherCurrents) / len(otherCurrents) if len(otherCurrents) > 0 else 0
    diff = abs(current - avgOtherCurrents)
    diffPercent = diff / avgOtherCurrents * 100 if avgOtherCurrents != 0 else 0
    logging.debug(f"Id: {id}, Current: {current}, Other currents: {otherCurrents}, Diff: {diff}, DiffPercent: {diffPercent}")
    return diffPercent

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
    # dc_currents.set_zero()
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