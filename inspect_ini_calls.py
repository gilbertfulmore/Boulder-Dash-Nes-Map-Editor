with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000
start_va = 0x4a1900
end_va = 0x4a1c00

# Let's inspect instructions and string references
# In Delphi: mov edx, string_va; mov ecx, string_va
import struct

def get_str(va):
    if va < 0x401000 or va >= 0x401000 + len(data):
        return None
    off = va - base
    # Delphi string: length is at off - 4 or off is shortstring (byte len at off)
    # Check null-terminated string at off
    end = data.find(b'\x00', off)
    if end != -1 and 0 < end - off < 50:
        try:
            s = data[off:end].decode('latin1')
            if s.isprintable(): return s
        except:
            pass
    return None

off = start_va - base
chunk = data[off:end_va-base]
for i in range(len(chunk)-5):
    curr_va = start_va + i
    b = chunk[i]
    if b == 0xba: # mov edx, imm32
        imm = struct.unpack('<I', chunk[i+1:i+5])[0]
        s = get_str(imm)
        if s:
            print(f"{hex(curr_va)}: MOV EDX, {hex(imm)} -> '{s}'")
    elif b == 0xb9: # mov ecx, imm32
        imm = struct.unpack('<I', chunk[i+1:i+5])[0]
        s = get_str(imm)
        if s:
            print(f"{hex(curr_va)}: MOV ECX, {hex(imm)} -> '{s}'")
    elif b == 0xe8: # call
        rel = struct.unpack('<i', chunk[i+1:i+5])[0]
        target = curr_va + 5 + rel
        if target in [0x408be4, 0x408c48, 0x408c84, 0x408cd8]:
            print(f"{hex(curr_va)}: CALL {hex(target)}")
