#!/usr/bin/env python3
"""
USB Device Information Script
Helps identify connected USB devices and their properties
"""

import subprocess
import os
import glob

def get_usb_device_info():
    """Get information about connected USB devices"""
    print("=== USB Device Information ===")
    print()
    
    # Check lsusb output
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Connected USB devices (lsusb):")
            for line in result.stdout.strip().split('\n'):
                if 'FT232' in line or 'FTDI' in line or 'RS485' in line:
                    print(f"  ★ {line}")  # Highlight relevant devices
                else:
                    print(f"    {line}")
        else:
            print("lsusb command failed")
    except Exception as e:
        print(f"Error running lsusb: {e}")
    
    print()
    
    # Check /dev/tty* devices
    print("Available serial devices:")
    tty_devices = glob.glob('/dev/tty*')
    for device in sorted(tty_devices):
        if any(x in device for x in ['ACM', 'USB', 'AMA']):
            print(f"  ★ {device}")
        else:
            print(f"    {device}")
    
    print()
    
    # Check specific device info
    devices_to_check = ['/dev/ttyACM0', '/dev/ttyUSB0', '/dev/ttyAMA0']
    for device in devices_to_check:
        if os.path.exists(device):
            print(f"Device {device} exists")
            try:
                # Get device permissions
                stat = os.stat(device)
                print(f"  Permissions: {oct(stat.st_mode)[-3:]}")
                
                # Try to get device info from udev
                try:
                    result = subprocess.run(['udevadm', 'info', '--name=' + device], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"  Device info:")
                        for line in result.stdout.split('\n'):
                            if any(x in line for x in ['ID_VENDOR', 'ID_MODEL', 'ID_SERIAL', 'DEVPATH']):
                                print(f"    {line}")
                except:
                    pass
                    
            except Exception as e:
                print(f"  Error getting info: {e}")
        else:
            print(f"Device {device} does not exist")
    
    print()

def check_serial_permissions():
    """Check if the current user has permission to access serial devices"""
    print("=== Serial Port Permissions ===")
    
    # Check if user is in dialout group
    try:
        result = subprocess.run(['groups'], capture_output=True, text=True)
        if result.returncode == 0:
            groups = result.stdout.strip().split()
            if 'dialout' in groups:
                print("✓ User is in 'dialout' group")
            else:
                print("✗ User is NOT in 'dialout' group")
                print("  Run: sudo usermod -a -G dialout $USER")
                print("  Then log out and log back in")
    except Exception as e:
        print(f"Error checking groups: {e}")
    
    print()

def suggest_troubleshooting():
    """Provide troubleshooting suggestions"""
    print("=== Troubleshooting Suggestions ===")
    print()
    print("1. Check connections:")
    print("   - Ensure RS485 converter is properly connected")
    print("   - Check A/B wiring (RS485 is differential)")
    print("   - Verify power supply to connected device")
    print()
    print("2. RS485 vs RS232:")
    print("   - RS485 uses differential signaling (A/B lines)")
    print("   - RS232 uses single-ended signaling")
    print("   - Make sure your device actually outputs RS485")
    print()
    print("3. Common issues:")
    print("   - Wrong baudrate (try 9600, 19200, 38400)")
    print("   - Incorrect parity/stop bits")
    print("   - A/B lines swapped")
    print("   - Device not configured to output NMEA")
    print()
    print("4. Test commands:")
    print("   - python3 test_rs485.py  # Test various configurations")
    print("   - python3 read_nmea.py   # Auto-detect baudrate")
    print("   - screen /dev/ttyACM0 9600  # Manual terminal test")
    print()

if __name__ == "__main__":
    get_usb_device_info()
    check_serial_permissions()
    suggest_troubleshooting()
