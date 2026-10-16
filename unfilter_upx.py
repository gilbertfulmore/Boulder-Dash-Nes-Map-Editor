import struct

with open('quarry_unpacked_v2.bin', 'rb') as f:
    data = bytearray(f.read())

# ESI = 0x401000
# In quarry_unpacked_v2.bin, offset 0 corresponds to VA 0x401000.
# So edi (VA) = 0x401000 + pos
# esi = 0x401000

pos = 0
count = 0x56f3
unfiltered = 0

while pos < len(data) - 5 and count > 0:
    b = data[pos]
    pos += 1
    if b == 0xe8 or b == 0xe9:
        if data[pos] == 0x1c:
            edi = 0x401000 + pos
            eax = struct.unpack('<I', data[pos:pos+4])[0]
            bl = data[pos+4]
            
            # shr ax, 8
            # rol eax, 16
            # xchg al, ah
            # Let's trace the bit manipulations:
            # eax has 4 bytes: B0, B1, B2, B3
            # Initially: B0 = 0x1c, B1, B2, B3
            # shr ax, 8 -> ax becomes B1 (high byte 0)
            # rol eax, 16 -> high word was (B3<<8 | B2), now in low word. low word was B1, now in high word.
            # xchg al, ah -> swaps low two bytes.
            # Let's do it exactly in Python simulating 32-bit registers:
            
            low16 = eax & 0xffff
            high16 = (eax >> 16) & 0xffff
            low16 = (low16 >> 8) & 0xffff
            eax = (high16 | (low16 << 16)) & 0xffffffff
            
            # xchg al, ah
            al = eax & 0xff
            ah = (eax >> 8) & 0xff
            eax = (eax & 0xffff0000) | (al << 8) | ah
            
            # sub eax, edi
            eax = (eax - edi) & 0xffffffff
            # add eax, esi (0x401000)
            eax = (eax + 0x401000) & 0xffffffff
            
            struct.pack_into('<I', data, pos, eax)
            pos += 4
            count -= 1
            unfiltered += 1

print(f"Unfiltered {unfiltered} calls/jumps (remaining count: {count})")

with open('quarry_perfect.bin', 'wb') as f:
    f.write(data)
print("Saved quarry_perfect.bin successfully!")
