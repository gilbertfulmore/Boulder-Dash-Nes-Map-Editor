with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]

tbl_off = 0x643
print("=== Bytecode Jump Table ===")
for cmd in range(50):
    ptr = prg[tbl_off + cmd*2] | (prg[tbl_off + cmd*2 + 1] << 8)
    byte_code = 0x90 + cmd
    if ptr < 0x8000 or ptr > 0xc000:
        break
    print(f"Cmd 0x{byte_code:02X} (index {cmd:2d}): target = ${ptr:04X} (PRG 0x{ptr - 0x8000:04X})")
