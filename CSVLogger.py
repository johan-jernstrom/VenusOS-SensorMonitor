import os
import csv
import time
from datetime import datetime
import logging

class CSVLogger:
    def __init__(self, directory, flush_interval=30):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing CSVLogger")
        if not os.path.isabs(directory):
            directory = os.path.abspath(directory)
        if not os.path.exists(directory):
            os.makedirs(directory)
            self.logger.info(f"Created directory: {directory}")
        self.directory = directory
        self.logger.info(f"Using directory: {self.directory}")
        self.buffer = []
        self.flush_interval = flush_interval
        self.last_flush_time = time.time()

    def ensure_file(self, filepath):
        if not os.path.exists(filepath):
            with open(filepath, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "current",
                    "voltage",
                    "b1_voltage",
                    "b1_current",
                    "b1_smoothed",
                    "b2_voltage",
                    "b2_current",
                    "b2_smoothed",
                    "b3_voltage",
                    "b3_current",
                    "b3_smoothed",
                ])

    def log(self, current, voltage, 
            b1_voltage, b1_current, b1_smoothed,
            b2_voltage, b2_current, b2_smoothed, 
            b3_voltage, b3_current, b3_smoothed):
        self.buffer.append([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            round(current, 2),
            round(voltage, 2),
            round(b1_voltage, 2),
            round(b1_current, 2),
            round(b1_smoothed, 2),
            round(b2_voltage, 2),
            round(b2_current, 2),
            round(b2_smoothed, 2),
            round(b3_voltage, 2),
            round(b3_current, 2),
            round(b3_smoothed, 2),
        ])
        now = time.time()
        if now - self.last_flush_time > self.flush_interval:
            self.flush()

    def flush(self):
        self.logger.debug("Flushing buffer to CSV file")
        if not self.buffer:
            return
        current_date = datetime.now().strftime("%Y%m%d")
        filename = 'dc_currents_' + current_date + '.csv'
        filepath = os.path.join(self.directory, filename)
        self.ensure_file(filepath)
        with open(filepath, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(self.buffer)
        self.buffer = []
        self.last_flush_time = time.time()

    def close(self):
        self.flush()