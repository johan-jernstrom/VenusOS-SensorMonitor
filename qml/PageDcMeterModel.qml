import QtQuick 1.1
import com.victron.velib 1.0

VisibleItemModel {
	property variant summary: [dcVoltage.text, dcCurrent.text, dcPower.text]

	property VBusItem dcVoltage: VBusItem { bind: service.path("/Dc/0/Voltage") }
	property VBusItem dcCurrent: VBusItem { bind: service.path("/Dc/0/Current") }
	property VBusItem dcPower: VBusItem { bind: service.path("/Dc/0/Power") }
	property VBusItem productId: VBusItem { bind: service.path("/ProductId") }
	property VBusItem monitorMode: VBusItem { bind: service.path("/Settings/MonitorMode") }

	property bool isSssDcEnergyMeter: productId.value === 0xB013

	function getServiceDescription(service)
	{
		switch(service.type)
		{
		case DBusService.DBUS_SERVICE_FUELCELL:
			return qsTr("Fuel cell")
		case DBusService.DBUS_SERVICE_ALTERNATOR:
			return qsTr("Alternator")
		case DBusService.DBUS_SERVICE_DCSYSTEM:
			return qsTr("DC system")
		}
		return monitorMode.valid ? monitorMode.text : qsTr("Load")
	}

	MbItemRow {
		description: getServiceDescription(service)
		values: [
			MbTextBlock { item: dcVoltage; width: 90; height: 25 },
			MbTextBlock { item: dcCurrent; width: 90; height: 25 },
			MbTextBlock { item: dcPower; width: 90; height: 25 }
		]
	}

	MbItemValue {
		description: qsTr("Temperature")
		item {
			bind: service.path("/Dc/0/Temperature")
			displayUnit: user.temperatureUnit
		}
		show: item.valid
	}

	MbItemValue {
		description: qsTr("Aux voltage")
		item.bind: service.path("/Dc/1/Voltage")
		show: item.valid
	}

	MbItemOptions {
		description: qsTr("Relay state")
		bind: service.path("/Relay/0/State")
		readonly: true
		possibleValues:[
			MbOption { description: qsTr("Off"); value: 0 },
			MbOption { description: qsTr("On"); value: 1 }
		]
		show: valid
	}

	MbItemOptions {
		id: alarmState
		description: qsTr("Alarm state")
		bind: service.path("/Alarms/Alarm")
		readonly: true
		possibleValues:[
			MbOption { description: qsTr("Ok"); value: 0 },
			MbOption { description: qsTr("Alarm"); value: 1 }
		]
		show: valid
	}

	MbSubMenu {
		description: qsTr("Alarms")
		subpage: Component {
			PageDcMeterAlarms {
				title: qsTr("Alarms")
				bindPrefix: service.path("")
			}
		}
		show: !isSssDcEnergyMeter
	}

	MbSubMenu {
		description: qsTr("History")
		subpage: Component {
			PageDcMeterHistory {
				title: qsTr("History")
				bindPrefix: service.path("")
			}
		}
		show: !isSssDcEnergyMeter
	}
	
	MbSpinBox {
			id: diffAlarm
			description: qsTr("Diff Alarm")
			item
			{
				bind: service.path("/DiffAlarm")
				unit: "%"
				decimals: 0
				step: 5
				min: 0
				max: 100
			}
			show: item.valid
			writeAccessLevel: User.AccessUser
        }

	MbSubMenu {
		description: qsTr("Device")
		subpage: Component {
			PageDeviceInfo {
				title: qsTr("Device")
				bindPrefix: service.path("")
			}
		}
	}
}
