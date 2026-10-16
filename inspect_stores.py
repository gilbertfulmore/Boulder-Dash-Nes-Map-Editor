import struct

with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000
start_va = 0x4a1900
end_va = 0x4a1c20

off = start_va - base
chunk = data[off:end_va-base]

for i in range(len(chunk)-6):
    curr_va = start_va + i
    b = chunk[i]
    # Check for mov [reg + disp], reg or mov [addr], reg
    # e.g., 89 84 ... or 89 44 ... or 89 0d ... or 89 15 ...
    if b == 0x89:
        modrm = chunk[i+1]
        mod = (modrm >> 6) & 3
        reg = (modrm >> 3) & 7
        rm = modrm & 7
        if mod == 2: # disp32
            disp = struct.unpack('<i', chunk[i+2:i+6])[0]
            print(f"{hex(curr_va)}: MOV [reg+{hex(disp)}], reg (modrm={hex(modrm)})")
        elif mod == 1: # disp8
            disp = chunk[i+2]
            print(f"{hex(curr_va)}: MOV [reg+{hex(disp)}], reg (modrm={hex(modrm)})")
        elif mod == 0 and rm == 5: # [disp32]
            addr = struct.unpack('<I', chunk[i+2:i+6])[0]
            print(f"{hex(curr_va)}: MOV [{hex(addr)}], reg")
