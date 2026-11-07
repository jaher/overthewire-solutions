# Vortex L3 — where the work stands

## The program (live binary, verified 2026-11-06)

`/vortex/vortex3`, mode 4750, setuid root, group vortex3, 11300 bytes,
md5 `17b12585fd1a15df97d13e84364744cf` (same md5 for `/vortex/vortex3` and a
copy taken in `/tmp`). The disassembly in `main.dis` was taken from that
copy: `objdump -d v3copy --start-address=0x8049176 --stop-address=0x80491f4`.

```c
int main(int argc, char **argv) {
    unsigned long *lp = &val;          /* ebp-0x10 */
    unsigned long **lpp = &lp;         /* ebp-0xc, starts as 0x804b210 */
    char buf[128];                     /* ebp-0x90 */
    if (argc != 2) exit(1);
    strcpy(buf, argv[1]);
    if (((unsigned long) lpp & 0xffff0000) != 0x08040000) exit(2);  /* mov $0,%ax; cmp $0x8040000 */
    tmp = *lpp;
    **lpp = (unsigned long) &buf;
    exit(0);
}
```

`buf` is at `ebp-0x90`, so the saved `ebp` is at `buf+0x94` (`buf+148`).
`lpp` sits at `buf+0x84` (= 132), `lp` at `buf+0x80` (= 128).

## Correction (2026-11-06)

A `main.dis` committed earlier described a "console bytecode VM" and a stack
walk. That does not match the binary: re-reading the same addresses from
several sessions, including a fresh copy of `/vortex/vortex3`, gives the
code above. The VM text is withdrawn, and so are the notes and scratch
scripts built on it. The `main` above is the only one the live binary runs.

## What the check allows

The check keeps only the high 16 bits of `lpp`. Any `lpp` of the form
`0x080Xxxxx` passes. When the check passes:

- `lpp[0]` must be readable (it is read into `tmp`).
- `lpp[0]` must be writable, because `**lpp = &buf` stores a stack address
  there.

The only mapped, writable page in the `0x0804` range is
`0x804b000..0x804bfff`. That page holds `.got.plt` (`0x804b1ec` up),
`.init_array`/`.fini_array` (around `0x804b208`), `.data` (`0x804b204`, the
`31370` test value) and `.bss` (to `0x804b218`).

## What is measured live

- argv length 1..131: exit 0 (no overflow reaches `ebp`).
- 132 and 133: the program stops instead of reaching the check. It ends up
  waiting (state `S`, `do_wait`) on a pipeline; a 139-byte file route gives
  exit 2, so the saved `ebp` low bytes decide between the two.
- 134 and up: exit 2. The saved `ebp` is overwritten, so `lpp` reads from
  inside `argv`; only a dword there that is `0x080Xxxxx` passes.
- 128 bytes + a `0x08..` dword as `lpp`: the process dies with `139` (a
  segfault). Over plain ssh the shell reports `Segmentation fault`; over
  the session channel the code is masked. The crash means the store `**lpp`
  went to non-writable memory, or that the GOT was changed where `exit`
  uses it.

## Measured GOT-slot map (128-byte overflow, lpp slot given)

| lpp | result |
|---|---|
| 0x804b1f0 (PLT0 GOT) | SIGSEGV |
| 0x804b1f4 (`_dl_runtime_resolve`) | SIGSEGV |
| 0x804b1f8 (`__libc_start_main`) | SIGSEGV |
| 0x804b1fc (`strcpy`) | SIGSEGV |
| 0x804b200 (`exit` JMP) | **exit 0**, no crash |
| 0x804b204 (`31370` data) | SIGSEGV |
| 0x804b208 / 0x804b210 / 0x804b214 | SIGSEGV |

No writable byte exists above 0x804b218, so after `**lpp = &buf` the only
dword on the stack walk that still fits the check is the `0x0804b200`
pointer itself (argv[8..11]): `**lpp` follows it to the same JMP slot, and
the walk ends there. Arguments longer than 150 bytes are refused by the
remote tools because their argument sanitizer rejects non-UTF-8 bytes.

## Open routes

1. **Make `exit` survive a GOT change.** Pointing `lpp` at a GOT slot makes
   `**lpp = &buf` (a stack address near `0x8ff..`) replace a resolved
   function pointer. The candidates and the frames they need:
   - `0x804b200` (`exit` itself): the next call is `exit(0)`; the stack
     frame would have to pass `*(&buf)`, i.e. the dword the store just wrote
     into `0x804b200` — a function pointer we do not control.
   - `0x804b1fc` (`strcpy`): not called again before `exit`.
   - `0x804b1f8` (`__libc_start_main`): not called again.
   - `0x804b1f4` (PLT0's GOT slot, `_dl_runtime_resolve`): unused once
     every relevant slot is already resolved.
   - `.init_array`/`.fini_array` around `0x804b208`: only run at image load
     and unload, not on `exit`.
   A writable page in the high half of the `0x0804` range (e.g. `.bss` at
   `0x804b210..`) cannot be reached: `lpp` must equal `0x080Xxxxx` with
   `X..` masked off (`mov $0,%ax`).
2. **Avoid `exit`.** If the store lands somewhere `exit` reads before it
   jumps (or if `exit` never runs), the stack address we wrote is never
   called.

## Files

- `main.dis` — verified disassembly (from `/tmp/v3copy`, md5 above).
- `relocs.txt` — GOT relocations and dynamic symbols.
- `sshraw.py` — runs a command string as vortex3 over plain ssh (argv
  list, no quoting).
- `ssh3.py` — same, legacy string form.
## Brute-force walk result (walk.py, 2026-11-06)

With `lpp = 0x804b200` (the only lpp that passes and whose store leaves the
JMP slot intact), the first step reads p = 0x804b200, so t = the slot dword
`0x0804xxxx`. That address is not mapped in the image, so the walk ends
there. No argv byte changes this.

Correction to a line above: the `0x0804b200` dword lives in argv[8..11]
(`&buf - 0x84 - 4`), not `&buf - 0x58 - 4`.

The walk cannot reach a low stack address: the low two bytes of `lpp` are
masked by the check, so `lpp` is always `0x0804xxxx` (inside argv), and a
low 32-bit stack pointer such as `0xffff8000` fails the check (`rc=2`).

`main` for an ordinary argument (length 1..131) cannot print anything; the
VM text that an earlier note described is not in the binary (`sim_main.py`
was deleted as unusable).

## Where it stands

Every route in the real binary now ends in one of three ways:

- `rc=2` (check rejected; the frame walk changed nothing),
- SIGSEGV (a store into read-only memory, or `exit` jumping through a
  corrupted slot),
- `rc=0` (the walk terminates at the JMP slot; no output).

It is recorded open. Not solved, not marked blocked.

## Public write-ups (2026-11-07)

- **Klaus (klaus.hohenpoelz.de/overthewire-vortex-wargame-level-3.html):** his build is
  the 2003 binary (`0x8048310`/`0x8097xx`). The trick: `lpp = 0x8048312`, the operand
  of `jmp DWORD PTR ds:0x80497xx` in the PLT stub; the 16-bit load reads `0x0804`,
  the suffix `0x97xx` gives an RWX page, `**lpp = &buf` lands in `exit@got.plt`, and
  `exit` jumps to shellcode in `buf`. Our build differs: the PLT lives in `.text`
  (`0x8049020`, R+E only, no RELRO), so the same construction faults. Live:
  `0x8049032`, `0x8049038`, `0x8049048`, `0x8049058` and `0x8049008` all give rc=2
  (the stub-word trick does not survive the frame check).
- **OverTheWire brief (vortex3.html):** "A Stack Overflow with a Difference"; the hint
  is to call `setuid(vortex4)` in the shellcode and notes that ctors/dtors "may no
  longer be writable"; built with `-Wl,-z,norelro`.

## Live environment findings (2026-11-07)

- `/tmp` is `drwxrwx-wt` (1773): writable and sticky, but **no read/search** for
  group/other, so it cannot be listed and a file can be opened only if its name is
  known and its mode allows it. `cp` into `/tmp/x` fails when `/tmp/x` already exists
  with a mode that denies writing.
- **`.data` is mapped MAP_SHARED** (`/tmp/l3w/vp` showed the patched bytes and
  `.data` took reloads): vortex3 can write into its own (and any adult's) binary
  file, e.g. `/vortex/vortex3` itself. This does not give a code path into the
  password file; `exit()` runs *before* this write, so a later run is needed,
  which is the same "second `vortex3` run" as the setuid check in the walk.
- **glibc 2.43 registers no destructors for this object** (`FINI_ARRAYSZ` 4 = one
  NULL entry), so `exit` has no dtor to run. A test patch registering a dtor
  (size 8 + .fini_array point at a write() cave in the RW page) segfaults on startup,
  because the zone from `0x804b000` to `0x804b0f8` is only part of the writable
  segment below the DT block: the cave at `0x804b170`/`0x804b150` sits inside the
  `DT_*` entries, which the loader reads.
