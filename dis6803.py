#!/usr/bin/env python3
"""
6803 / 6801 disassembler.
Linearer Disassembler mit Sprungverfolgung und Annotation.

Usage: ./dis6803.py firmware.bin > dis.lst
"""
import sys, struct
from collections import deque

# Opcode table: opcode -> (mnemonic, addressing_mode)
# Modes: 'inh', 'imm8', 'imm16', 'dir', 'ext', 'idx', 'rel'
OPS = {}

# Inherent (1 byte)
INH = {
    0x01: 'NOP',  0x04: 'LSRD', 0x05: 'ASLD', 0x06: 'TAP', 0x07: 'TPA',
    0x08: 'INX',  0x09: 'DEX',  0x0A: 'CLV',  0x0B: 'SEV', 0x0C: 'CLC',
    0x0D: 'SEC',  0x0E: 'CLI',  0x0F: 'SEI',  0x10: 'SBA', 0x11: 'CBA',
    0x16: 'TAB',  0x17: 'TBA',  0x19: 'DAA',  0x1B: 'ABA',
    0x30: 'TSX',  0x31: 'INS',  0x32: 'PULA', 0x33: 'PULB',
    0x34: 'DES',  0x35: 'TXS',  0x36: 'PSHA', 0x37: 'PSHB',
    0x38: 'PULX', 0x39: 'RTS',  0x3A: 'ABX',  0x3B: 'RTI',
    0x3C: 'PSHX', 0x3D: 'MUL',  0x3E: 'WAI',  0x3F: 'SWI',
    0x40: 'NEGA', 0x43: 'COMA', 0x44: 'LSRA', 0x46: 'RORA',
    0x47: 'ASRA', 0x48: 'ASLA', 0x49: 'ROLA', 0x4A: 'DECA',
    0x4C: 'INCA', 0x4D: 'TSTA', 0x4F: 'CLRA',
    0x50: 'NEGB', 0x53: 'COMB', 0x54: 'LSRB', 0x56: 'RORB',
    0x57: 'ASRB', 0x58: 'ASLB', 0x59: 'ROLB', 0x5A: 'DECB',
    0x5C: 'INCB', 0x5D: 'TSTB', 0x5F: 'CLRB',
}
for op, m in INH.items():
    OPS[op] = (m, 'inh')

# Branches (rel, 2 bytes)
REL = {
    0x20: 'BRA', 0x21: 'BRN', 0x22: 'BHI', 0x23: 'BLS',
    0x24: 'BCC', 0x25: 'BCS', 0x26: 'BNE', 0x27: 'BEQ',
    0x28: 'BVC', 0x29: 'BVS', 0x2A: 'BPL', 0x2B: 'BMI',
    0x2C: 'BGE', 0x2D: 'BLT', 0x2E: 'BGT', 0x2F: 'BLE',
    0x8D: 'BSR',
}
for op, m in REL.items():
    OPS[op] = (m, 'rel')

# Indexed-only (idx, 2 bytes)
IDX_ONLY = {
    0x60: 'NEG',  0x63: 'COM',  0x64: 'LSR',  0x66: 'ROR',
    0x67: 'ASR',  0x68: 'ASL',  0x69: 'ROL',  0x6A: 'DEC',
    0x6C: 'INC',  0x6D: 'TST',  0x6E: 'JMP',  0x6F: 'CLR',
}
for op, m in IDX_ONLY.items():
    OPS[op] = (m, 'idx')

# Extended-only (ext, 3 bytes)
EXT_ONLY = {
    0x70: 'NEG',  0x73: 'COM',  0x74: 'LSR',  0x76: 'ROR',
    0x77: 'ASR',  0x78: 'ASL',  0x79: 'ROL',  0x7A: 'DEC',
    0x7C: 'INC',  0x7D: 'TST',  0x7E: 'JMP',  0x7F: 'CLR',
}
for op, m in EXT_ONLY.items():
    OPS[op] = (m, 'ext')

# Accumulator/memory operations (high nibble 8/9/A/B for A reg, C/D/E/F for B reg)
# Low nibble determines operation
# High nibble determines addressing: 8=imm, 9=dir, A=idx, B=ext (for A reg)
#                                    C=imm, D=dir, E=idx, F=ext (for B reg)
ACC_OPS = {
    0: 'SUB', 1: 'CMP', 2: 'SBC', 3: None,  # 3 = SUBD (A side imm only) or ADDD/SUBD
    4: 'AND', 5: 'BIT', 6: 'LDA', 7: 'STA',
    8: 'EOR', 9: 'ADC', 0xA: 'ORA', 0xB: 'ADD',
    0xC: None, 0xD: None, 0xE: None, 0xF: None,
}

def addrmode_for(hi):
    return {8:'imm8', 9:'dir', 0xA:'idx', 0xB:'ext',
            0xC:'imm8', 0xD:'dir', 0xE:'idx', 0xF:'ext'}.get(hi)

def reg_for(hi):
    return 'A' if hi in (8,9,0xA,0xB) else 'B'

# Build accumulator ops
for hi in (8, 9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF):
    reg = reg_for(hi)
    mode = addrmode_for(hi)
    for lo in range(0x10):
        op = (hi << 4) | lo
        # Special cases for low nibble C, D, E, F
        if lo == 0xC:  # CPX (A side) / LDD (B side)
            mnem = 'CPX' if reg == 'A' else 'LDD'
            OPS[op] = (mnem, 'imm16' if mode == 'imm8' else mode)
        elif lo == 0xD:
            if reg == 'A' and mode == 'imm8':  # 0x8D = BSR (already covered)
                continue
            elif reg == 'A':  # 0x9D=??, AD=JSR idx, BD=JSR ext
                mnem = 'JSR'
                OPS[op] = (mnem, mode)
            else:  # B side: STD
                if mode == 'imm8':  # 0xCD reserved
                    continue
                OPS[op] = ('STD', mode)
        elif lo == 0xE:  # LDS (A) or LDX (B)
            mnem = 'LDS' if reg == 'A' else 'LDX'
            OPS[op] = (mnem, 'imm16' if mode == 'imm8' else mode)
        elif lo == 0xF:  # STS (A) or STX (B); not valid for imm
            if mode == 'imm8':
                continue
            mnem = 'STS' if reg == 'A' else 'STX'
            OPS[op] = (mnem, mode)
        elif lo == 3:
            # SUBD (A imm only) / ADDD (A others?) — actually SUBD is 0x83
            # 0x83 SUBD imm16, 0x93 SUBD dir, 0xA3 SUBD idx, 0xB3 SUBD ext
            # 0xC3 ADDD imm16, 0xD3 ADDD dir, 0xE3 ADDD idx, 0xF3 ADDD ext
            mnem = 'SUBD' if reg == 'A' else 'ADDD'
            OPS[op] = (mnem, 'imm16' if mode == 'imm8' else mode)
        elif ACC_OPS.get(lo):
            mnem = ACC_OPS[lo] + reg
            OPS[op] = (mnem, mode)

# Special: 0x8C is CPX imm16 (handled above but verify)
OPS[0x8C] = ('CPX', 'imm16')
OPS[0x9C] = ('CPX', 'dir')
OPS[0xAC] = ('CPX', 'idx')
OPS[0xBC] = ('CPX', 'ext')
OPS[0xCC] = ('LDD', 'imm16')
OPS[0xDC] = ('LDD', 'dir')
OPS[0xEC] = ('LDD', 'idx')
OPS[0xFC] = ('LDD', 'ext')
OPS[0xDD] = ('STD', 'dir')
OPS[0xED] = ('STD', 'idx')
OPS[0xFD] = ('STD', 'ext')
OPS[0x8E] = ('LDS', 'imm16')
OPS[0x9E] = ('LDS', 'dir')
OPS[0xAE] = ('LDS', 'idx')
OPS[0xBE] = ('LDS', 'ext')
OPS[0xCE] = ('LDX', 'imm16')
OPS[0xDE] = ('LDX', 'dir')
OPS[0xEE] = ('LDX', 'idx')
OPS[0xFE] = ('LDX', 'ext')
OPS[0x9F] = ('STS', 'dir')
OPS[0xAF] = ('STS', 'idx')
OPS[0xBF] = ('STS', 'ext')
OPS[0xDF] = ('STX', 'dir')
OPS[0xEF] = ('STX', 'idx')
OPS[0xFF] = ('STX', 'ext')

LENGTHS = {'inh':1, 'imm8':2, 'imm16':3, 'dir':2, 'ext':3, 'idx':2, 'rel':2}

def disasm_one(data, file_off, base_addr):
    """Disassemble one instruction at data[file_off]. Returns (length, asm_str, target_or_none)."""
    if file_off >= len(data):
        return 1, '???', None
    op = data[file_off]
    spec = OPS.get(op)
    cpu_pc = base_addr + file_off
    if spec is None:
        return 1, f'.byte ${op:02X}    ; unknown opcode', None
    mnem, mode = spec
    L = LENGTHS[mode]
    if file_off + L > len(data):
        return 1, f'.byte ${op:02X}    ; truncated', None
    target = None
    if mode == 'inh':
        asm = f'{mnem}'
    elif mode == 'imm8':
        v = data[file_off+1]
        asm = f'{mnem:5s} #${v:02X}'
        if 32 <= v < 127:
            asm += f"   ; {chr(v)!r}"
    elif mode == 'imm16':
        v = (data[file_off+1] << 8) | data[file_off+2]
        asm = f'{mnem:5s} #${v:04X}'
    elif mode == 'dir':
        v = data[file_off+1]
        asm = f'{mnem:5s} ${v:02X}'
    elif mode == 'ext':
        v = (data[file_off+1] << 8) | data[file_off+2]
        asm = f'{mnem:5s} ${v:04X}'
        # Track jump target for code follow
        if mnem in ('JMP', 'JSR'):
            target = v
    elif mode == 'idx':
        v = data[file_off+1]
        asm = f'{mnem:5s} ${v:02X},X'
    elif mode == 'rel':
        offset = data[file_off+1]
        if offset >= 0x80:
            offset -= 0x100
        target = cpu_pc + 2 + offset
        asm = f'{mnem:5s} ${target:04X}'
    return L, asm, target

# 6803 SCI / IO register names
IO_NAMES = {
    0x00: 'P1DDR', 0x01: 'P2DDR', 0x02: 'P1DR', 0x03: 'P2DR',
    0x04: 'P3DDR', 0x05: 'P4DDR', 0x06: 'P3DR', 0x07: 'P4DR',
    0x08: 'TCSR',  0x09: 'CTRH',  0x0A: 'CTRL',  0x0B: 'OCR1H',
    0x0C: 'OCR1L', 0x0D: 'ICR1H', 0x0E: 'ICR1L', 0x0F: 'P3CSR',
    0x10: 'RMCR',  0x11: 'TRCSR', 0x12: 'RDR',   0x13: 'TDR',
    0x14: 'RAMCR',
}

def annotate_io(asm):
    """Replace ${02} etc in dir-addressing with IO name comment."""
    import re
    m = re.match(r'^(\w+\s+)\$([0-9A-F]{2})$', asm)
    if m and int(m.group(2),16) in IO_NAMES:
        name = IO_NAMES[int(m.group(2),16)]
        return asm + f'  ; {name}'
    return asm

def main():
    if len(sys.argv) < 2:
        print('Usage: dis6803.py firmware.bin [base_addr_hex]', file=sys.stderr)
        sys.exit(1)
    data = open(sys.argv[1], 'rb').read()
    base = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0xE000

    # Code follow: BFS from entry points
    visited = set()  # file offsets that are instruction starts
    queue = deque()

    # Entry points from vectors
    def add_vec(off_in_file):
        if off_in_file + 1 < len(data):
            tgt = (data[off_in_file] << 8) | data[off_in_file+1]
            if base <= tgt < base + len(data):
                queue.append(tgt - base)
    # Vectors at $FFF0..$FFFF (file offset 0x1FF0..0x1FFF if base=$E000)
    for vec_off in range(len(data)-16, len(data), 2):
        add_vec(vec_off)

    # Manual jump tables: $E16D bis $E1A2 (single-letter cmd dispatch),
    # $E5DB bis... ('*'-subcommand dispatch). Lese alle Einträge und queue sie.
    def queue_table(file_off_start, file_off_end):
        for fo in range(file_off_start, file_off_end, 2):
            if fo + 1 < len(data):
                tgt = (data[fo] << 8) | data[fo+1]
                if base <= tgt < base + len(data):
                    queue.append(tgt - base)
    # E16D..E1A2 (Tabelle für A-Z, 26 Einträge à 2 Byte = 52 Byte)
    queue_table(0x16D, 0x16D + 52)
    # E5DB..E5DB+52 ('*'-Subcommand-Tabelle)
    queue_table(0x5DB, 0x5DB + 52)

    # Trace
    while queue:
        off = queue.popleft()
        while off < len(data) and off not in visited:
            visited.add(off)
            L, asm, target = disasm_one(data, off, base)
            op = data[off]
            # Stop tracing on unconditional control transfers
            if op in (0x39, 0x3B, 0x3F, 0x20, 0x6E, 0x7E):  # RTS, RTI, SWI, BRA, JMP idx, JMP ext
                if target is not None and base <= target < base + len(data):
                    queue.append(target - base)
                break
            # Conditional branches: also queue the target
            if op in REL and op not in (0x20, 0x8D):  # conditional branches
                if target is not None and base <= target < base + len(data):
                    queue.append(target - base)
            # JSR: queue target
            if op in (0xAD, 0xBD):
                if target is not None and base <= target < base + len(data):
                    queue.append(target - base)
            # BSR
            if op == 0x8D and target is not None and base <= target < base + len(data):
                queue.append(target - base)
            off += L

    # Output linear listing
    print(f'; 6803 disassembly of {sys.argv[1]} (base ${base:04X})')
    print(f'; Visited {len(visited)} instruction starts')
    print()

    off = 0
    while off < len(data):
        cpu_pc = base + off
        if off in visited:
            L, asm, target = disasm_one(data, off, base)
            asm = annotate_io(asm)
            bytes_str = ' '.join(f'{b:02X}' for b in data[off:off+L])
            print(f'{cpu_pc:04X}: {bytes_str:8s}  {asm}')
            off += L
        else:
            # Data byte
            b = data[off]
            ch = chr(b) if 32 <= b < 127 else '.'
            print(f'{cpu_pc:04X}: {b:02X}        .byte ${b:02X}     ; {ch!r}')
            off += 1

if __name__ == '__main__':
    main()
