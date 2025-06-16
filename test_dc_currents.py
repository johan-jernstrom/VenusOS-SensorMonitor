import logging
from dc_currents import DcCurrents
import time

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s")
    print("Initializing DcCurrents for manual test...")
    dc = DcCurrents()
    try:
        for i in range(10):
            print(f"\n--- Read {i+1} ---")
            smoothed = dc.read_currents()
            for ch, val in smoothed.items():
                print(f"Channel {ch}: {val.get():.2f} A (smoothed)")
            time.sleep(1)
    finally:
        dc.shutdown()
        print("Shutdown complete.")
