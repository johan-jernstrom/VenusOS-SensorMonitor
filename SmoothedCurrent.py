class SmoothedCurrent:
    """
    A class to maintain a smoothed current value over a sliding window.
    It keeps track of the last N values and the quality of the value defined as the percentage of non-None values in the window.
    """

    def __init__(self, window_size=10):
        self.buffer = [0] * window_size
        self.quality = [0] * window_size  # Quality of the current values in the buffer
        self.BaselineCurrent = 0  # latest baseline current
        self.Voltage = 0         # latest battery voltage

    def update(self, value, baseline_current, voltage):
        """Updates the buffer with a new value, removing the oldest value.
        Also updates the BaselineCurrent and Voltage
        If the value is None, the value is not added to the buffer, and the quality is decreased.
        """
        if value is None:
            self.quality.pop(0)
            self.quality.append(0)  # Append a quality of 0 for None values
            return
        self.quality.pop(0)
        self.quality.append(100)  # Assume new value has full quality
        self.buffer.pop(0)
        self.buffer.append(value)
        self.BaselineCurrent = baseline_current
        self.Voltage = voltage

    def get_value(self, default=None):
        """Returns the average of the values in the buffer.
        This is a simple moving average.
        """
        if not self.buffer:
            return default

        if self.get_quality() < 50:
            # If the quality is below 50%, return the default value
            return default
        return sum(self.buffer) / len(self.buffer)

    def get_quality(self):
        """Returns the percentage quality of the values in the buffer.
        The quality is calculated as the average of the quality values in the buffer.
        """
        if not self.quality:
            return 0
        return sum(self.quality) / len(self.quality)

    def get_baseline_current(self):
        """
        Returns the current BaselineCurrent value for this instance.
        """
        return self.BaselineCurrent

    def get_voltage(self):
        """
        Returns the current Voltage value for this instance.
        """
        return self.Voltage