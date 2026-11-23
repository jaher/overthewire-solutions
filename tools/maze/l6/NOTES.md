# Maze L6 — solved (2026-11-23)

## The program (live binary, md5 a3dde0a162510d0c142a6d33f66084d0)

`/maze/maze6`, mode 4750, setuid **maze7**, group maze6, 14352 bytes, ELF
32-bit i386 with debug_info, not stripped.

main (0x80491d6):

```c
int main(int argc, char **argv) {
    char buf[0x100];                     /* ebp-0x104 */
    if (argc != 3) { printf("%s file2write2 string\n", argv[0]); exit(-1); }
    FILE *f = fopen(argv[1], "a");
    if (!f) { perror("fopen"); exit(-1); }
    strcpy(buf, argv[2]);                /* UNBOUNDED — buf is 0x100 */
    memfrob(buf, strlen(buf));           /* XOR every byte with 42 */
    fprintf(f, "%s : %s\n", argv[1], buf);
    exit(0);                             /* saved EIP never used! */
}
```

## The two key facts

1. **`strcpy(buf[0x100], argv[2])` is an unbounded stack overflow** (no canary in
   main). memfrob XORs the copy with 42 — an involution, so argv[2] = payload^42
   and the payload arrives INTACT in buf at fprintf time. NULs are allowed in
   buf: a raw 0x00 rides in argv[2] as 0x2a/'*'; the raw payload must avoid 0x2a.
2. **main ends with `exit(0)`** — the saved EIP is dead. Reachable targets:
   (a) the `FILE *f` at buf+0x100 (FSOP), (b) the caller frame — argc/argv/envp
   at buf+0x10c..0x114 and the argv[] array at buf+0x1d0 — all smashed by the
   overflow and needing REPAIR.

## The exploit chain (`exploit.py` v5, `sc.py`)

- Repair the caller frame inside the payload: argc=3; argv ptr -> the argv[]
  array rebuilt at buf+0x1d0; argv[1] -> a **path string copied INTO the payload**
  (buf+0x284) — critical: pointing argv[1] at the original path string left the
  fprintf line length env-dependent and the GOT write always missed.
- Replace `f` with a **fake FILE = byte-exact 0xa0-byte copy of the real heap
  FILE struct** (gdb-dumped) with only _IO_write_base/_IO_write_ptr redirected
  to `exit@GOT - 24` and write_end/buf_end extended. The first attempt used a
  0x8c-byte copy which MISSED the vtable pointer at offset 0x94 -> `Fatal error:
  glibc detected an invalid stdio handle` (SIGABRT from _IO_vtable_check). The
  REAL vtable (_IO_file_jumps, 0xf7fa27a8) passes glibc's vtable check.
- fprintf memcpy's the line `path : buf` into the GOT: line offset 24 (= 21-byte
  path + " : ") lands **buf[0..4] exactly on exit@GOT (0x804b228)**.
- buf[0..4] = `leave; ret` (libc+0x1af32e). After fprintf, `call exit@plt ->
  jmp *exit@GOT` runs leave;ret: esp := ebp (= buf+0x104, our value), pop ebp,
  ret -> eip = [buf+0x108] = the shellcode at buf+0x2a0.
- Shellcode (`sc.py`, 71 bytes, NUL-free and 0x2a-free): open/read/write
  `/etc/maze_pass/maze7` to fd 1 — no execve (dash would drop the euid).
- buf address: measured 0xffffd824 via `gdb --args` with LINES/COLUMNS unset,
  then swept ±0x400 in 4-byte steps; **HIT at buf = 0xffffd7e4**.

## Result (live)

```
$ python3 - <<PY  (build payload for buf=0xffffd7e4)
$ /maze/maze6 /run/screen/l6/wP.txt <payload>
-> GOT overwritten -> leave;ret pivot -> shellcode:
ckkOx2s4Ev
```

Password `ckkOx2s4Ev` verified by ssh login as maze7 (uid=15007, cat matches).

## Files

- `maze6` — the live binary copy (md5 above).
- `exploit.py` — the FSOP/GOT-overwrite payload builder (v5).
- `sc.py` — the pass-reading shellcode builder.
- `fastsweep.py` / `probe.py` / `test_write.py` — the sweep/diagnostic helpers.
- `NOTES.md` — this file.
