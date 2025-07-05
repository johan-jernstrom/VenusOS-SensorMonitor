import serial
import time

# Common baudrates for NMEA and RS485 devices
baudrates = [4800, 9600, 19200, 38400, 57600, 115200]

def invert_signal(data):
    """Invert signal bits (for Garmin-style inverted TTL signals)"""
    if not data:
        return data
    # XOR each byte with 0xFF to invert all bits
    return bytes([b ^ 0xFF for b in data])

def test_baudrate(port, baudrate, invert=False):
    """Test a specific baudrate and return if valid NMEA data is found"""
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
        
        invert_str = " (INVERTED)" if invert else ""
        print(f"Testing baudrate {baudrate}{invert_str}...")
        
        # Read a few lines to test
        for i in range(10):
            line = ser.readline()
            if line:
                # Apply signal inversion if needed
                if invert:
                    line = invert_signal(line)
                
                try:
                    decoded_line = line.decode('ascii', errors='ignore').strip()
                    if decoded_line.startswith('$') and len(decoded_line) > 10:
                        print(f"SUCCESS: Found NMEA data at {baudrate} baud{invert_str}!")
                        print(f"Sample: {decoded_line}")
                        ser.close()
                        return True
                except:
                    pass
        
        ser.close()
        return False
        
    except Exception as e:
        print(f"Error testing baudrate {baudrate}{invert_str}: {e}")
        return False

def read_nmea_data(port, baudrate, invert=False):
    """Read NMEA data with the correct baudrate"""
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
        
        invert_str = " (INVERTED)" if invert else ""
        print(f"Reading NMEA sentences on port {port} with baudrate {baudrate}{invert_str}, press Ctrl+C to stop...")
        
        while True:
            line = ser.readline()
            if line:
                # Apply signal inversion if needed
                if invert:
                    line = invert_signal(line)
                
                print("Raw bytes:", line)
                try:
                    # Try ASCII decoding first
                    decoded_line = line.decode('ascii').strip()
                    if decoded_line.startswith('$'):
                        print("✓ NMEA:", decoded_line)
                    elif decoded_line:
                        print("ASCII:", decoded_line)
                except UnicodeDecodeError:
                    # Try UTF-8 as fallback
                    try:
                        decoded_line = line.decode('utf-8', errors='ignore').strip()
                        if decoded_line:
                            print("UTF-8:", decoded_line)
                    except:
                        # Show hex representation for debugging
                        hex_data = ' '.join(f'{b:02x}' for b in line[:50])  # First 50 bytes
                        print("HEX:", hex_data)
                        
    except KeyboardInterrupt:
        ser.close()
        print("\nStopped.")
    except Exception as e:
        print(f"Error: {e}")
        if 'ser' in locals():
            ser.close()

# Main execution
if __name__ == "__main__":
    port = '/dev/ttyACM0'
    
    print("=== NMEA/RS485 Serial Port Debugger ===")
    print(f"Testing port: {port}")
    print()
    
    # First, try to auto-detect the correct baudrate
    print("1. Auto-detecting baudrate...")
    found_baudrate = None
    found_invert = False
    
    # Test both normal and inverted signals for each baudrate
    for baudrate in baudrates:
        # Test normal signal first
        if test_baudrate(port, baudrate, invert=False):
            found_baudrate = baudrate
            found_invert = False
            break
        
        # Test inverted signal (Garmin-style)
        if test_baudrate(port, baudrate, invert=True):
            found_baudrate = baudrate
            found_invert = True
            break
        
        time.sleep(0.5)
    
    if found_baudrate:
        invert_str = " (INVERTED)" if found_invert else ""
        print(f"\n2. Using detected baudrate: {found_baudrate}{invert_str}")
        read_nmea_data(port, found_baudrate, found_invert)
    else:
        print("\n2. No NMEA data detected. Testing with 4800 baud inverted (Garmin standard)...")
        print("This will show raw data to help diagnose the issue.")
        read_nmea_data(port, 4800, invert=True)