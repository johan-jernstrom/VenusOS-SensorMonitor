from dataclasses import dataclass
from datetime import datetime

@dataclass
class SensorData:
    battery: float = None
    temperature: float = None
    humidity: float = None
    timestamp: datetime = datetime.now()