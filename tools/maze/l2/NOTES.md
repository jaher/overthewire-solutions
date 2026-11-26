# Maze L2 — solved (2026-11-22)

## The program (live binary, md5 6ecff0cde7d203a8bec2cbf29f638f92)

`/maze/maze1` … rather `/maze/maze2`, mode 4750, setuid maze3, group
maze1, 12668 bytes, with debug_info, not stripped.  main (wrap_main,
reconstructed from objdump with debug info):

```c
int main(int argc, char **argv) {
    char buf[12];
    void (*fp)(void) = &buf;         /* lea eax,[ebp-0xc]; mov [ebp-0x10],eax */
    if (argc != 2) exit(1);
    strncpy(buf, argv[1], 8);        /* call 0x8049060 */
    fp();                            /* mov eax,[ebp-0x10]; call eax  — runs buf[0] */
}
```

`GNU_STACK RWE` (confirmed live: `readelf -l` shows RWE; an `int3`
carried in argv[1] traps).  ASLR off (`randomize_va_space = 0`).

## The last session's puzzle, diagnosed

Two independent bugs produced the "mechanism works but elevation
missing / empty output" symptoms:

1. **The 85-byte pass-reading shellcode built its path backwards.**  Its
   path dwords were pushed in forward chunk order (`/etc`, `/maz`,
   `e_pa`, `ss/m`, `aze3`), so the stack held the string
   `nib/hs//3ezam/ssap_ezam/cte/` (last push at the lowest address).
   `open()` got ENOENT — hence the empty output.  Decoded from the
   scratch `sc.bin` (85 bytes, NUL-free) this session.
2. **The marker-shell HIT condition could never match.**  The 23-byte
   `execve("/bin//sh")` stage ran, but the spawned dash drops the
   elevated euid after execve (no `-p`), so `id` printed uid=15002 and
   the sweep's `uid=15003` HIT condition never fired.

## The exploit

- Corrected shellcode (sc.asm): `open("/etc/maze_pass/maze3")` via
  `int 0x80`, read into a stack buffer, write the count to fd 1 and
  fd 2, exit.  Path dwords pushed in **reverse chunk order** (`aze3`
  first, `/etc` last) so the stack holds `/etc/maze_pass/maze3\0`
  forward.  71 bytes, NUL-free.
- Delivery: `strncpy(argv[1], 8)` copies the first 8 bytes of argv[1]
  into `buf`; 8 bytes = `push imm32; ret` (6 bytes + 2 pad), NUL-free
  for 0xffffXXXX targets, jumping to an absolute address.
- The shellcode lives in the env (`P='A'*2000 + SC`, passed as BYTES to
  avoid utf-8 mangling) with a huge NOP sled absorbing the layout
  uncertainty.
- Target sweep: for every 4-byte-aligned address in 0xffffc000.. and
  upward, build argv[1] = `\x68 <target> \xc3 AA`, run `/maze/maze2`,
  stop when anything is printed.

## Result

Sweep hit at **0xffffd6e8** in the recorded interactive run (an earlier
trial hit `0xffffd6e0` — the env-sled address varies with the environment
layout), dumping 10 bytes twice — the fd1+fd2 signature —
`pKWcO3NfC6`, the maze3 password.  Verified by ssh login as maze3
(uid=15003, cat /etc/maze_pass/maze3 matches).  Recording:
recordings/maze/L2.cast.

## Standard-v2 re-record (2026-11-26, attempt 13 — the committed cast)

The re-record surfaced two more payload-encoding lessons (see the
"Recorded-run debugging discipline" note in CLAUDE.md):

1. **`sub esp, 0x80` is NOT NUL-free.**  The imm32 form encodes
   `81 EC 80 00 00 00` — three NUL bytes that the sweep's
   `$(cat sc.bin)` silently stripped ("ignored null byte in input"),
   truncating the sled.  The imm8 form `sub esp, 0x7f`
   (`83 EC 7F`) is NUL-free; the read count (0x2000 via `mov dh`)
   still covers the 12-byte password.  sc.bin dropped 81 → 78 bytes.
2. **The sweep's argv must carry the full 8 bytes**: `\x68` push
   opcode + target LE + `\xc3` ret + `AA` pad.  Attempt 12 built only
   the 4 raw address bytes (`A=$(printf "\x${T:6:2}...")`), so every
   run executed garbage and died silently — stage 1 and 2 both
   "missed" without a single error message.

Final recorded run: stage 1 (0xffffd6d0–0xffffd720) missed — the layout
shifted because the sled shrank — stage 2 hit **0xffffd010**, password
printed twice (fd1+fd2).  Verified live as maze3 (uid=15003).  The
post-solve verbatim replay (Rule 4b) reproduced the vi sessions to the
same `:wq` markers (sc.asm 41L/1355B, sweep.sh 27L/957B) and the same
solved state via tools/replay/gen_ptyrun2.py + the two-phase wrapper.

## Files

- `sc.asm` / `sc.bin` — the corrected shellcode (this run's bytes).
- `maze2` — the live binary copy (md5 above).
- `helper.c`, `sweep2.sh`, `sweep3.py` — the earlier pinning attempts
  (the helper's layout did not match maze2's, hence the earlier SIGSEGV
  sweep).
