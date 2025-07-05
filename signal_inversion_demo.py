#!/usr/bin/env python3
"""
Signal Inversion Demonstration
Shows how Garmin inverted TTL signals work
"""

def invert_signal(data):
    """Invert signal bits (for Garmin-style inverted TTL signals)"""
    if not data:
        return data
    # XOR each byte with 0xFF to invert all bits
    return bytes([b ^ 0xFF for b in data])

def demonstrate_inversion():
    """Demonstrate signal inversion with example data"""
    print("=== Signal Inversion Demonstration ===")
    print()
    
    # Example NMEA sentence
    nmea_sentence = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
    nmea_bytes = nmea_sentence.encode('ascii')
    
    print("1. Original NMEA sentence:")
    print(f"   Text: {nmea_sentence}")
    print(f"   Hex:  {' '.join(f'{b:02x}' for b in nmea_bytes)}")
    print()
    
    # Simulate what Garmin sends (inverted)
    inverted_bytes = invert_signal(nmea_bytes)
    print("2. Inverted signal (what Garmin sends):")
    print(f"   Hex:  {' '.join(f'{b:02x}' for b in inverted_bytes)}")
    
    # Try to decode inverted signal directly (should fail)
    try:
        decoded_inverted = inverted_bytes.decode('ascii', errors='ignore')
        print(f"   Text: {repr(decoded_inverted)} (garbled!)")
    except:
        print("   Text: (cannot decode - binary garbage)")
    print()
    
    # Invert back to get original
    restored_bytes = invert_signal(inverted_bytes)
    restored_text = restored_bytes.decode('ascii')
    print("3. After inverting back:")
    print(f"   Text: {restored_text}")
    print(f"   Hex:  {' '.join(f'{b:02x}' for b in restored_bytes)}")
    print()
    
    # Show the bit-level inversion
    print("4. Bit-level inversion example:")
    original_byte = ord('$')  # Dollar sign (0x24)
    inverted_byte = original_byte ^ 0xFF  # Invert all bits
    
    print(f"   Original '$' = 0x{original_byte:02x} = {original_byte:08b}b")
    print(f"   Inverted     = 0x{inverted_byte:02x} = {inverted_byte:08b}b")
    print(f"   Restored '$' = 0x{(inverted_byte ^ 0xFF):02x} = {(inverted_byte ^ 0xFF):08b}b")
    print()
    
    print("This explains why your original data looked like binary garbage!")
    print("The Garmin device is sending inverted TTL signals.")
    print()

def analyze_your_data():
    """Analyze the garbled data from your original output"""
    print("=== Analyzing Your Original Data ===")
    print()
    
    # Sample of your original garbled data
    garbled_hex = "d8 5a 96 76 eb 97 a7 9b 9b 9d a7 9f 9f ab 91 9d e5 eb 70 8b 7d"
    garbled_bytes = bytes.fromhex(garbled_hex.replace(' ', ''))
    
    print("Your original garbled data (first 21 bytes):")
    print(f"   Hex: {garbled_hex}")
    print()
    
    # Try inverting it
    inverted_bytes = invert_signal(garbled_bytes)
    print("After signal inversion:")
    print(f"   Hex: {' '.join(f'{b:02x}' for b in inverted_bytes)}")
    
    # Try to decode
    try:
        decoded = inverted_bytes.decode('ascii', errors='ignore')
        print(f"   Text: {repr(decoded)}")
        
        # Check if it looks like NMEA
        if '$' in decoded or decoded.startswith('$'):
            print("   *** This looks like NMEA data! ***")
        else:
            print("   Still not NMEA format, might need different baudrate")
    except:
        print("   Still cannot decode")
    print()

if __name__ == "__main__":
    demonstrate_inversion()
    analyze_your_data()
    
    print("=== Next Steps ===")
    print("1. Run: python3 test_rs485.py")
    print("   This will test both normal and inverted signals")
    print()
    print("2. Run: python3 read_nmea.py")
    print("   This will auto-detect baudrate and inversion")
    print()
    print("3. Hardware solution (recommended):")
    print("   - Use a 74HC04 inverter chip as shown in the article")
    print("   - Or use an RS485 converter with inversion capability")
    print()
    print("4. Alternative software workaround:")
    print("   - Use the updated scripts that handle inversion")
    print("   - May not work perfectly due to USB converter limitations")
