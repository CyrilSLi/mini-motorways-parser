while True:
    fix64 = input("Enter a fix64 hex value: ")
    try:
        # Convert the hex string to bytes
        fix64_bytes = bytes.fromhex(fix64)
        if len(fix64_bytes) != 8:
            raise ValueError("Input must be exactly 8 bytes (16 hex characters).")
        
        # Convert the bytes to a fix64 value
        fix64_value = int.from_bytes(fix64_bytes, byteorder="little", signed=True) / (1 << 32)
        
        print(f"Fix64 value: {fix64_value}")
    except ValueError as e:
        print(f"Invalid input: {e}")