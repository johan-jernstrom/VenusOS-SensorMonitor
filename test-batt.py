from dbus_battery_reader import DbusBatteryReader

if __name__ == "__main__":
    try:
        reader = DbusBatteryReader()
        voltage, current = reader.get_batt_voltage_current()
        print(f"Battery Voltage: {voltage:.2f} V")
        print(f"Battery Current: {current:.2f} A")
    except Exception as e:
        print(f"Error reading from dbus: {e}")
        import traceback
        traceback.print_exc()
