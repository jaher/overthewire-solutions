# Maze L7 — SOLVED (2026-11-23)

## The program (live binary, md5 b493aca59eeb119a97915b1c0d27c422)

`/maze/maze7`, mode 4750, setuid **maze8**, group maze7, 14796 bytes, i386 with
debug_info. An ELF section-header printer: `Print_Shdrs` (0x80491f6) + `main`
(0x804932d). Imports: open/read/lseek/malloc/free/printf/puts/putchar/close/
exit. **GNU_STACK RWE**, ASLR off on the lab; heap is rw-p (NOT executable).

main reads the first 0x34 bytes of `argv[1]` into a 0x34-byte stack buffer,
then calls `Print_Shdrs(fd, e_shoff, e_shstrndx, e_shnum, e_shentsize)` —
callee args: `[ebp+0x8]=fd, +0xc=e_shoff, +0x10=e_shstrndx, +0x14=e_shnum,
+0x18=e_shentsize` — ALL attacker-controlled by the crafted file:

- `lseek(fd, e_shoff)`; `malloc(e_shnum*40)`; read the shdr array;
- `sh = buf + e_shstrndx*40`; `lseek(sh->sh_offset)`; `malloc(sh->sh_size)`;
  read the string table;
- print loop `i = 0 .. e_shnum` **inclusive** (jle, off-by-one); per iteration
  **`read(fd, ebp-0x3c, e_shentsize)`** into the 0x34-byte stack buffer, then
  `printf("%2d: %-16s\t0x%08x\t0x%04x\n", i, strtab+sh_name, sh_addr, sh_size)`
  — the printed shdr is the freshly re-read buffer;
- `free(strtab); free(shdrbuf)` on pointers at `ebp-0x14`/`ebp-0xc`, INSIDE the
  overflow window.

## The vulnerability

On real ELFs e_shentsize=40: safe. Crafted: **e_shentsize=0x100** → the loop
read overflows the 0x34-byte buffer (saved EIP at buf+0x40). The read starts
at e_shoff, so the shdr-array region of the file IS the payload (NULs fine).
One iteration runs: the read rewrites the loop counter i→1, i++ → 2 > e_shnum=1
exits cleanly.

Overflow layout (buffer = Print_Shdrs ebp-0x3c):
```
0x00 shdr0 (sh_name=0, sh_offset=STRTAB_OFF, sh_size=STRTAB_SZ)
0x28 [ebp-0x14] free(strtab)  -> real malloc'd strtab (repair, 0x804d050)
0x30 [ebp-0xc]  free(shdrbuf) -> real malloc'd shdrbuf (repair, 0x804d020)
0x34 [ebp-0x8]  i -> 1 (exit loop)
0x38 saved ebx, 0x3c saved ebp (don't care)
0x40 saved EIP -> buf+0x60 (shellcode IN the payload, stack is RWE)
0x60 69-byte open/read/write /etc/maze_pass/maze8 -> fd 1 shellcode
```
strtab starts with a NUL so printf's `%s` (strtab+sh_name) prints an empty
string — a long garbage `%s` crashed inside vfprintf during early attempts.

## Debugging story (the three traps)

1. **Payload offset**: first build appended the payload at 0x34 while e_shoff
   was 0x40 — every control dword landed 12 bytes early (free() saw 1/0, EIP
   was 0). Fix: pad the header to e_shoff.
2. **Non-exec heap**: EIP first pointed at the malloc'd strtab (heap is rw-p →
   SIGSEGV). Move the shellcode into the stack payload itself.
3. **Free-list clobber**: with the shellcode at strtab+0 the freed chunk's fd/bk
   overwrote its first bytes. With it on the stack this no longer matters.
   (Plus a push-order byte-swap bug in the shellcode path string and a
   fffb/ffff typo — both caught by single-stepping in gdb.)
4. **Address sweep**: the loop buffer is env-dependent (gdb: 0xffffdb34).
   Sweeping buf ±0x1000 step 4 INSIDE one live ssh session hit **0xffffdb08** (exec env); a sweep inside the recorded pty session hit **0xffffd308** (used for the cast).

## Result (live)

```
$ /maze/maze7 /run/screen/l7/evil.elf   (e_shentsize=256 crafted ELF)
avdYfGdEvv
```

Password `avdYfGdEvv` verified by ssh login as maze8 (uid=15008, cat matches).

## Files

- `maze7` — live binary copy. `gen.py` — exploit-file generator (v2).
- `sc.bin`/`sc.hex` — 69-byte pass-reading shellcode (chunks pushed so the
  stack holds '/etc/maze_pass/maze8\0' forward).
- `probe.elf` — EIP→0xbad0b0b0 probe used to measure the repair addresses.
- `NOTES.md` — this file. Recording: `recordings/maze/L7.cast`.
