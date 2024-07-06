#!/usr/bin/env python
import logging
from gi.repository import GLib # type: ignore
from dbus.mainloop.glib import DBusGMainLoop # type: ignore
from cpu_temp import CPUTemp
from w1_temps import W1Temps
from dc_currents import DcCurrents
from alarm import AlarmBuzzer
from dbus_service import DCSourceService, TemparatureService

tempServices = {}
currentServices = {}

# Create the sensors that will be monitored and exposed to dbus
cpu_temp = CPUTemp()
w1_temps = W1Temps()
dc_currents = DcCurrents()
alarm = AlarmBuzzer()

def update_temp_services():
    newTemps = w1_temps.read_temperatures()
    newTemps['rpi'] = cpu_temp.read_temperature()
    for id in newTemps:
        create_temp_service_if_not_exists(id)
        tempServices[id].update(newTemps[id])
        alarm.check_value(newTemps[id], tempServices[id].settings['HighTempAlarm'], id)

    # disconnect services that are no longer available
    for id in tempServices:
        if id not in newTemps:
            tempServices[id].disconnect()
    
    return True

def create_temp_service_if_not_exists(id):
    if id not in tempServices:
        conn = 'CPU' if id == 'rpi' else 'Wire'
        instance = 1000 + len(tempServices)
        tempServices[id] = TemparatureService(conn, id, instance)

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

    # make initial call
    update_temp_services()
    # and then every 5 seconds
    GLib.timeout_add_seconds(5, lambda: update_temp_services())

    # make initial call
    # dc_currents.set_zero()
    update_current_services()
    # and then every 1 seconds
    GLib.timeout_add_seconds(1, lambda: update_current_services())

    logging.info('Connected to dbus, and switching over to GLib.MainLoop() (= event based)')
    mainloop.run()
    logging.info('Exiting...')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s")
    main() 