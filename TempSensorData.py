from dataclasses import dataclass
from datetime import datetime

@dataclass
class TempSensorData():
    """
    Class to store temperature and humidity data read from temperature sensors.
    """
    id: str = None
    connection: str = None
    battery: float = None
    temperature: float = None
    humidity: float = None
    timestamp: datetime = datetime.now()

    def __str__(self):
        return f"Connection: {self.connection}, Battery: {self.battery}, Temperature: {self.temperature}, Humidity: {self.humidity}, Timestamp: {self.timestamp}"