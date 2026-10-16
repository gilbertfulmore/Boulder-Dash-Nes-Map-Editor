with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]

OPCODES = {
    0x00: ('BRK', 1), 0x01: ('ORA ($%02X,X)', 2), 0x05: ('ORA $%02X', 2), 0x06: ('ASL $%02X', 2),
    0x08: ('PHP', 1), 0x09: ('ORA #$%02X', 2), 0x0a: ('ASL A', 1), 0x0d: ('ORA $%04X', 3), 0x0e: ('ASL $%04X', 3),
    0x10: ('BPL $%04X', 2), 0x18: ('CLC', 1), 0x20: ('JSR $%04X', 3), 0x24: ('BIT $%02X', 2),
    0x25: ('AND $%02X', 2), 0x26: ('ROL $%02X', 2), 0x28: ('PLP', 1), 0x29: ('AND #$%02X', 2),
    0x2a: ('ROL A', 1), 0x2c: ('BIT $%04X', 3), 0x2d: ('AND $%04X', 3), 0x30: ('BMI $%04X', 2),
    0x38: ('SEC', 1), 0x40: ('RTI', 1), 0x48: ('PHA', 1), 0x49: ('EOR #$%02X', 2),
    0x4a: ('LSR A', 1), 0x4c: ('JMP $%04X', 3), 0x50: ('BVC $%04X', 2), 0x60: ('RTS', 1),
    0x65: ('ADC $%02X', 2), 0x68: ('PLA', 1), 0x69: ('ADC #$%02X', 2), 0x6a: ('ROR A', 1),
    0x6c: ('JMP ($%04X)', 3), 0x70: ('BVS $%04X', 2), 0x78: ('SEI', 1), 0x81: ('STA ($%02X,X)', 2),
    0x84: ('STY $%02X', 2), 0x85: ('STA $%02X', 2), 0x86: ('STX $%02X', 2), 0x88: ('DEY', 1),
    0x8a: ('TXA', 1), 0x8c: ('STY $%04X', 3), 0x8d: ('STA $%04X', 3), 0x8e: ('STX $%04X', 3),
    0x90: ('BCC $%04X', 2), 0x91: ('STA ($%02X),Y', 2), 0x94: ('STY $%02X,X', 2), 0x95: ('STA $%02X,X', 2),
    0x98: ('TYA', 1), 0x99: ('STA $%04X,Y', 3), 0x9a: ('TXS', 1), 0x9d: ('STA $%04X,X', 3),
    0xa0: ('LDY #$%02X', 2), 0xa1: ('LDA ($%02X,X)', 2), 0xa2: ('LDX #$%02X', 2), 0xa4: ('LDY $%02X', 2),
    0xa5: ('LDA $%02X', 2), 0xa6: ('LDX $%02X', 2), 0xa8: ('TAY', 1), 0xa9: ('LDA #$%02X', 2),
    0xaa: ('TAX', 1), 0xac: ('LDY $%04X', 3), 0xad: ('LDA $%04X', 3), 0xae: ('LDX $%04X', 3),
    0xb0: ('BCS $%04X', 2), 0xb1: ('LDA ($%02X),Y', 2), 0xb4: ('LDY $%02X,X', 2), 0xb5: ('LDA $%02X,X', 2),
    0xb8: ('CLV', 1), 0xb9: ('LDA $%04X,Y', 3), 0xba: ('TSX', 1), 0xbc: ('LDY $%04X,X', 3),
    0xbd: ('LDA $%04X,X', 3), 0xc0: ('CPY #$%02X', 2), 0xc5: ('CMP $%02X', 2), 0xc6: ('DEC $%02X', 2),
    0xc8: ('INY', 1), 0xc9: ('CMP #$%02X', 2), 0xca: ('DEX', 1), 0xcc: ('CPY $%04X', 3),
    0xcd: ('CMP $%04X', 3), 0xd0: ('BNE $%04X', 2), 0xd8: ('CLD', 1), 0xe0: ('CPX #$%02X', 2),
    0xe5: ('SBC $%02X', 2), 0xe6: ('INC $%02X', 2), 0xe8: ('INX', 1), 0xe9: ('SBC #$%02X', 2),
    0xea: ('NOP', 1), 0xec: ('CPX $%04X', 3), 0xee: ('INC $%04X', 3), 0xf0: ('BEQ $%04X', 2)
}

def disasm(code, start_pc, count=80):
    pc = 0
    instructions = 0
    while pc < len(code) and instructions < count:
        curr_pc = start_pc + pc
        op = code[pc]
        if op in OPCODES:
            name, length = OPCODES[op]
            if length == 1:
                print(f"${curr_pc:04X}:  {name}")
            elif length == 2:
                arg = code[pc+1]
                if name.startswith('B'):
                    rel = arg if arg < 0x80 else arg - 0x100
                    target = curr_pc + 2 + rel
                    print(f"${curr_pc:04X}:  {name[:3]} ${target:04X}")
                else:
                    print(f"${curr_pc:04X}:  {name % arg}")
            elif length == 3:
                arg = code[pc+1] | (code[pc+2] << 8)
                print(f"${curr_pc:04X}:  {name % arg}")
            pc += length
        else:
            print(f"${curr_pc:04X}:  .db ${op:02X}")
            pc += 1
        instructions += 1

print("--- 0x87fb ---")
disasm(prg[0x7fb:0x950], 0x87fb, 120)
