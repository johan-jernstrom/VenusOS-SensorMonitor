#!/bin/bash
# Installation script for NMEA/RS485 testing tools

echo "Installing required packages for NMEA/RS485 testing..."

# Install Python serial library
echo "Installing pyserial..."
pip3 install pyserial

# Make Python scripts executable
chmod +x read_nmea.py
chmod +x test_rs485.py
chmod +x device_info.py

echo "Installation complete!"
echo ""
echo "Usage:"
echo "  python3 device_info.py      # Check connected devices"
echo "  python3 test_rs485.py       # Test RS485 configurations"
echo "  python3 read_nmea.py        # Auto-detect NMEA data"
echo ""
echo "If you get permission errors, run:"
echo "  sudo usermod -a -G dialout \$USER"
echo "  Then log out and log back in"
