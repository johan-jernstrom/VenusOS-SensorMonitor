# VenusOS Sensor Monitor

This script monitors various sensors and exposes their readings through D-Bus.
Currently, the following sensors are supported:'
- CPU temperature
- 1-wire temperature sensors
- DC current sensors

The primary purpose of this driver is to monitor the temperature and current sensors connected to the electric propulsion system of a boat. 
The temperature sensors are used to monitor the temperature of the batteries and motor, and the current sensors are used to monitor the current draw from each battery connected in parallel.
An alarm is triggered if the temperature or current exceeds a certain threshold or if the current draw from one battery is significantly different from the others.

## Dependencies

This project uses the following Python libraries:
- gpiozero
- adafruit-circuitpython-ads1x15

plus some built in libraries, included in Venus Os:
- vedbus
- ve_utils 

## Installation

### Pre requisites

You need to setup some depenacies on your VenusOS first

1) SSH to IP assigned to venus device
1) Resize/Expand file system
    ```bash
    /opt/victronenergy/swupdate-scripts/resize2fs.sh
    ```
1) Update opkg
    ```bash
    opkg update
    ```
1) Install git
    ```bash
    opkg install git
    ```
1) Clone VenusOS-SensorMonitor repo<br/>
    ```bash
    cd /data/
    git clone https://github.com/johan-jernstrom/VenusOS-SensorMonitor.git
    cd VenusOS-SensorMonitor
    ```
1) Install pip
    ```bash
    opkg install python3-pip
    ```
1) Install all dependencies, eg:
    ```bash
    pip3 install RPi.GPIO
    pip3 install gpiozero
    pip3 install adafruit-circuitpython-ads1x15
    ```
    **NOTE**: More dependencies might be required to be installed. Test my manually starting the program after install and verify it runs ok:
    ```bash
    python /data/VenusOS-SensorMonitor/monitor.py
    ```

NOTE: Developed and tested on a Raspberry Pi 3B running Venus OS 3.14 LARGE

### Configuration

None.

### Installing the service and UI

Executing the install script installes the service and the UI automatically.

```bash
bash install.sh
```

## Running the Client

After successful install, the driver will be run automatically after each boot by the daemon service by the Venus OS.

To run the driver manually, type `python monitor.py` in a shell. 