import logging
from dc_currents import DcCurrents
import time

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s")
    
    dc_currents = DcCurrents()
    logging.info("DcCurrents initialized. Starting to read smoothed values...")
    try:
        while True:
            smoothed_values = dc_currents.get_latest_smoothed_values()
            logging.info(f"Smoothed Values: {smoothed_values}")
            time.sleep(1)  # Adjust the sleep time as needed
    except KeyboardInterrupt:
        logging.info("Stopping DcCurrents...")
    except Exception as e:
        logging.exception("An error occurred in DcCurrents: %s", e)
    finally:
        dc_currents.shutdown()
        logging.info("DcCurrents shutdown complete.")