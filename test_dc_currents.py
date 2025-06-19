from dc_currents import DcCurrents
import time

if __name__ == "__main__":
    
    dc_currents = DcCurrents()
    print("DcCurrents initialized. Starting to read and log current values...")
    try:
        while True:
            smoothed_values = dc_currents.get_latest_smoothed_values()
            for channel, smoothed_current in smoothed_values.items():
                print(f"Channel {channel}: Smoothed Current: {smoothed_current.get_value()}, "
                      f"Baseline Current: {smoothed_current.get_baseline_current()}, "
                      f"Voltage: {smoothed_current.get_voltage()}, "
                      f"Quality: {smoothed_current.get_quality()}")
            time.sleep(1)  # Adjust the sleep time as needed
    except KeyboardInterrupt:
        print("Stopping DcCurrents due to keyboard interrupt.")
    except Exception as e:
        print(f"An error occurred in DcCurrents: {e}")
    finally:
        dc_currents.shutdown()
        print("DcCurrents shutdown complete.")