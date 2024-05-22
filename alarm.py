#!/usr/bin/env python
import logging
import time
from gpiozero import Buzzer, Button # type: ignore

class AlarmBuzzer:
    # buzzerPin = 20 #38 is GPIO20
    # buttonPin = 16 #36 is GPIO16
    def __init__(self, buzzerPin = 20, buttonPin = 16):
        self.logger = logging.getLogger(__name__) # create logger
        
        self.buzzer = Buzzer(buzzerPin) # set up buzzer
        self.button = Button(buttonPin, hold_time=3) # set up button
        self.button.when_pressed = self.silence_all_alarms
        self.button.when_held = self.test_buzzer

        self.active_alarms = {}    # dictionary to keep track of sensors that are currently active
        self.silence_time = 30*60 # seconds to keep sensor silent after it has been activated

    def test_buzzer(self):
        if self.buzzer.is_active:
            self.logger.info("Buzz already active")
            return
        self.buzzer.beep(on_time=.25, off_time=.25, n=None, background=True)    # start same buzz as in CheckSensorValue to test the buzzer
    
    def silence_all_alarms(self):
        self.logger.info("Silencing all active alarms")
        self.buzzer.off()
        self.buzzer.beep(on_time=1, off_time=1, n=1, background=True)   # beep once to indicate that all active alarms have been silenced
        # set all time values in dict to current time meaning all currently active sensors will be turned off for X seconds
        for key in self.active_alarms:
            self.active_alarms[key] = time.time()
            self.logger.info("Sensor " + str(key) + " has been turned off for " + str(self.silence_time) + " seconds")

    def check_value(self, value, valueThreshold, sensorId):
        self.logger.debug("Checking sensor value " + str(value) + " with threshold " + str(valueThreshold) + " for sensor " + str(sensorId))
        # check if value, valueThreshold or sensorId is None or empty string 
        if value is None or valueThreshold is None or sensorId is None or value == "" or valueThreshold == "" or sensorId == "":
            self.logger.debug("AlarmBuzzer: value, valueThreshold or sensorId is None or empty string")
            return
        try:
            value = float(value)
            valueThreshold = float(valueThreshold)
        except:
            self.logger.error("AlarmBuzzer: Error converting value " + str(value) + " or valueThreshold " + str(valueThreshold) + " to float")
            return

        if value > valueThreshold:
            self.logger.info("Alarm for sensor " + str(sensorId))

            # check dictonary value for sensorId and if it is there then check if it is within self.SensorSilenceTime seconds
            if sensorId in self.active_alarms and time.time() - self.active_alarms[sensorId] < self.silence_time:
                self.logger.debug("Sensor " + str(sensorId) + " has already started buzz within " + str(self.silence_time) + " seconds")
                return
            
            # add sensorId to dict with current time
            self.active_alarms[sensorId] = time.time()
            self.logger.info("Sensor " + str(sensorId) + " has active alarm")

            # start buzz on separate thread unless it is already started
            if self.buzzer.is_active:
                self.logger.info("Buzz already active")
                return
            self.buzzer.beep(on_time=.25, off_time=.25, n=None, background=True)
        else:
            self.logger.debug("Sensor " + str(sensorId) + " has normal value")
            if sensorId in self.active_alarms:
                self.active_alarms.pop(sensorId)   # remove sensorId from dict if value is normal to make it buzz if value goes high again
                self.logger.info("Sensor " + str(sensorId) + " has returned to normal value")
                # if no sensor is buzzing then turn off the buzzer
                if len(self.active_alarms) == 0:
                    self.buzzer.off()
                    self.logger.info("Buzzer has been turned off since no alarm is active")
