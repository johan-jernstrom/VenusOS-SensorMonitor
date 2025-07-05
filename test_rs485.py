#!/usr/bin/env python3
"""
RS485 Configuration Test Script
This script helps diagnose RS485 communication issues
"""

import serial
import time
import sys

def invert_signal(data):
    """Invert signal bits (for Garmin-style inverted TTL signals)"""
    if not data:
        return data
    # XOR each byte with 0xFF to invert all bits
    return bytes([b ^ 0xFF for b in data])

def test_rs485_device(port='/dev/ttyACM0'):
    """Test RS485 device with various configurations"""
    
    print("=== RS485 Device Test ===")
    print(f"Testing port: {port}")
    print()
    
    # Common RS485/NMEA configurations
    # Based on Garmin documentation: 5V TTL, inverted signals
    configs = [
        # Standard NMEA configurations
        {'baudrate': 4800, 'bytesize': 8, 'parity': 'N', 'stopbits': 1, 'invert': False},  # NMEA standard
        {'baudrate': 4800, 'bytesize': 8, 'parity': 'N', 'stopbits': 1, 'invert': True},   # NMEA inverted (Garmin)
        {'baudrate': 38400, 'bytesize': 8, 'parity': 'N', 'stopbits': 1, 'invert': False}, # NMEA high speed
        {'baudrate': 38400, 'bytesize': 8, 'parity': 'N', 'stopbits': 1, 'invert': True},  # NMEA high speed inverted
        
        # Other common configurations
        {'baudrate': 9600, 'bytesize': 8, 'parity': 'N', 'stopbits': 1, 'invert': False},
        {'baudrate': 9600, 'bytesize': 8, 'parity': 'N', 'stopbits': 1, 'invert': True},
        {'baudrate': 19200, 'bytesize': 8, 'parity': 'N', 'stopbits': 1, 'invert': False},
        {'baudrate': 19200, 'bytesize': 8, 'parity': 'N', 'stopbits': 1, 'invert': True},
    ]
    
    for i, config in enumerate(configs):
        invert_flag = config.get('invert', False)
        config_desc = f"{config['baudrate']} baud, {config['bytesize']}{config['parity']}{config['stopbits']}"
        if invert_flag:
            config_desc += " (INVERTED)"
        
        print(f"Test {i+1}: {config_desc}")
        
        try:
            # Convert parity to pyserial format
            parity_map = {'N': serial.PARITY_NONE, 'E': serial.PARITY_EVEN, 'O': serial.PARITY_ODD}
            
            ser = serial.Serial(
                port=port,
                baudrate=config['baudrate'],
                bytesize=config['bytesize'],
                parity=parity_map[config['parity']],
                stopbits=config['stopbits'],
                timeout=2,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            
            # Read some data
            data_found = False
            for attempt in range(5):
                line = ser.readline()
                if line:
                    data_found = True
                    
                    # Apply signal inversion if needed
                    if invert_flag:
                        line = invert_signal(line)
                    
                    print(f"  Raw: {line}")
                    
                    # Try to decode
                    try:
                        decoded = line.decode('ascii', errors='ignore').strip()
                        if decoded and decoded.startswith('$'):
                            print(f"  ✓ NMEA: {decoded}")
                            print(f"  *** POSSIBLE MATCH! ***")
                            # If we found NMEA data, let's read a few more lines
                            print("  Reading more data...")
                            for extra in range(3):
                                extra_line = ser.readline()
                                if extra_line:
                                    if invert_flag:
                                        extra_line = invert_signal(extra_line)
                                    try:
                                        extra_decoded = extra_line.decode('ascii', errors='ignore').strip()
                                        if extra_decoded.startswith('$'):
                                            print(f"    ✓ {extra_decoded}")
                                    except:
                                        pass
                        elif decoded and len(decoded) > 3:
                            print(f"  Text: {decoded}")
                    except:
                        pass
                    
                    # Show hex for debugging
                    hex_data = ' '.join(f'{b:02x}' for b in line[:20])
                    print(f"  Hex: {hex_data}")
                    break
            
            if not data_found:
                print("  No data received")
            
            ser.close()
            print()
            
        except Exception as e:
            print(f"  Error: {e}")
            print()
    
    print("=== Manual Test Mode ===")
    print("Starting manual test with 9600 baud (most common for RS485)")
    print("Press Ctrl+C to stop")
    
    try:
        ser = serial.Serial(
            port=port,
            baudrate=9600,
            bytesize=8,
            parity=serial.PARITY_NONE,
            stopbits=1,
            timeout=1,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
        
        byte_count = 0
        while True:
            data = ser.read(1)  # Read one byte at a time
            if data:
                byte_count += 1
                byte_val = data[0]
                
                # Show readable character or hex
                if 32 <= byte_val <= 126:  # Printable ASCII
                    char = chr(byte_val)
                    print(f"Byte {byte_count}: 0x{byte_val:02x} ('{char}')")
                else:
                    print(f"Byte {byte_count}: 0x{byte_val:02x}")
                
                # Check for NMEA sentence start
                if byte_val == ord('$'):
                    print("*** NMEA sentence start detected! ***")
                    # Try to read the rest of the line
                    line = ser.readline()
                    if line:
                        try:
                            full_line = '$' + line.decode('ascii', errors='ignore').strip()
                            print(f"Full NMEA: {full_line}")
                        except:
                            print(f"Full line hex: {' '.join(f'{b:02x}' for b in line)}")
                
                # Limit output to prevent spam
                if byte_count > 200:
                    print("... (limiting output, press Ctrl+C to stop)")
                    time.sleep(1)
                    byte_count = 0
            
    except KeyboardInterrupt:
        print("\nStopped manual test.")
        ser.close()
    except Exception as e:
        print(f"Error in manual test: {e}")

if __name__ == "__main__":
    port = '/dev/ttyACM0'
    if len(sys.argv) > 1:
        port = sys.argv[1]
    
    test_rs485_device(port)
