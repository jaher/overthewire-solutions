def make_table():
    tbl = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (c >> 1) ^ (0xedb88320 if c & 1 else 0)
        tbl.append(c)
    return tbl
TBL = make_table()

def crc7(data, crc=0):
    for b in data:
        crc = TBL[(crc ^ b) & 0xff] ^ (crc >> 8)
    return crc

def solve_linear(deltas, want):
    basis = {}
    for i in range(32):
        v, t = deltas[i], 1 << i
        while v:
            top = v.bit_length() - 1
            if top in basis:
                bv, bt = basis[top]
                v ^= bv; t ^= bt
            else:
                basis[top] = (v, t)
                break
    v, t = want, 0
    while v:
        top = v.bit_length() - 1
        if top not in basis:
            return None
        bv, bt = basis[top]
        v ^= bv; t ^= bt
    return t

def patch4(base, target):
    zeros_crc = crc7(base + b'\x00\x00\x00\x00')
    deltas = []
    for i in range(32):
        p = bytearray(4)
        p[i // 8] |= 1 << (i % 8)
        deltas.append(crc7(base + bytes(p)) ^ zeros_crc)
    want = target ^ zeros_crc
    sel = solve_linear(deltas, want)
    if sel is None: return None
    return bytes([(sel >> (8*i)) & 0xff for i in range(4)])

if __name__ == '__main__':
    base = b'test'
    patch = patch4(base, 0xe1ca95ee)
    print('patch:', patch)
    if patch:
        full = base + patch
        print('crc7(full):', hex(crc7(full)), 'target: 0xe1ca95ee')
