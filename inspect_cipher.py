with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000

for va in [0x49f348, 0x49e170, 0x49e014]:
    off = va - base
    print(f"=== Function at {hex(va)} ===")
    chunk = data[off:off+80]
    print(' '.join(f"{b:02x}" for b in chunk))
