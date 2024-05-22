#!/bin/sh

# set permissions
chmod -R 777 /data/VenusOS-SensorMonitor/

# create a symlink to the service directory to make it start automatically by the daemon manager
ln -s /data/VenusOS-SensorMonitor/service /service/VenusOS-SensorMonitor
ln -s /data/VenusOS-SensorMonitor/service /opt/victronenergy/service/VenusOS-SensorMonitor

echo "Service symlink created"

# backup old PageTemperatureSensor.qml once. New firmware upgrade will remove the backup
if [ ! -f /opt/victronenergy/gui/qml/PageTemperatureSensor.qml.backup ]; then
    cp /opt/victronenergy/gui/qml/PageTemperatureSensor.qml /opt/victronenergy/gui/qml/PageTemperatureSensor.qml.backup
    echo "Backup of PageTemperatureSensor.qml created"
fi

# backup old PageDcMeterModel.qml once. New firmware upgrade will remove the backup
if [ ! -f /opt/victronenergy/gui/qml/PageDcMeterModel.qml.backup ]; then
    cp /opt/victronenergy/gui/qml/PageDcMeterModel.qml /opt/victronenergy/gui/qml/PageDcMeterModel.qml.backup
    echo "Backup of PageDcMeterModel.qml created"
fi

# copy altered PageTemperatureSensor.qml
cp qml/PageTemperatureSensor.qml /opt/victronenergy/gui/qml/
cp qml/PageDcMeterModel.qml /opt/victronenergy/gui/qml/
echo "Copied new and updated qml pages"

# restart gui
svc -t /service/gui
echo "GUI restarted"

# start service
svc -t /service/VenusOS-SensorMonitor
echo "Service started"
