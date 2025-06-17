class SmoothedValue:
    """
    A class to maintain a smoothed value over a sliding window.
    It keeps track of the last N values and the quality of the value defined as the percentage of non-None values in the window.
    """

    def __init__(self, initial_value=0, window_size=10):
        self.buffer = [initial_value] * window_size
        self.quality = [0] * window_size  # Quality of each value, 0-100

    def update(self, value):
        """Updates the buffer with a new value, removing the oldest value.
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

    def set(self, value):
        """Sets the current value and updates the buffer."""
        self.buffer = [value] * len(self.buffer)

    def get(self, default=None):
        """Returns the average of the values in the buffer.
        This is a simple moving average.
        """
        if not self.buffer:
            return default
        
        if self.get_quality()< 50:
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