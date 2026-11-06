# Vortex L3 — where the work stands

## The program (live binary, 2026-11-06)

`/vortex/vortex3` is setuid root, mode 4750, group vortex3.  It is the
0xbadc0ded #02 source compiled for i386 (md5 `17b12585fd1a15df97d13e84364744cf`,
11300 bytes, PIE, entry 0x8049060, image base 0x55555000).  Full disassembly
of `main` is in `main.dis`, the relocations in `relocs.txt`:

```c
int main(int argc, char **argv) {
    static unsigned long val = 31370;      /* .data 0x804b20c — never written */
    unsigned long *lp = &val;              /* ebp-0x10 */
    unsigned long **lpp = &lp;             /* ebp-0xc, starts as 0x804b210 */
    char buf[128];
    if (argc != 2) exit(1);
    strcpy(buf, argv[1]);
    if (((unsigned long) lpp & 0xffff0000) != 0x08040000) exit(2);   /* mov $0,%ax; cmp $0x8040000 */
    tmp = *lpp;                            /* ebp-0x14 */
    **lpp = (unsigned long) &buf;
    exit(0);
}
```

`buf` is at `ebp-0x90`, so the saved `ebp` lives at `buf+0x94` = `buf+148`.
The check only keeps the high 16 bits of `lpp`, so an overflow can make it
`0x080Xxxxx` and `lpp` has to point at readable writable memory.

## Live behaviour (re-measured 2026-11-06, plain ssh, stdin /dev/null)

| argv[1] length | exit |
|---|---|
| 1..131 | 0 |
| 132, 133 | freezes reading stdin before the check |
| 134..160 | 2 |
| 128 "A" + any `0x08..xx xx xx` dword | data abort (139) |

Length 132 touches the low byte of saved `ebp` (`buf+148`); 133 touches the
next.  The program then waits for stdin EOF instead of running the check:
`sleep 30 | vortex3 <arg>` leaves it stopped with `arg_start` 0x454 below the
top of the stack, and the program consumes stdin to EOF.  A shell
`$(cat file)` replaces NUL, and `$()` results above 127 bytes go through a
temporary file, so exactly 140 or 141 bytes reach the program on the
`$(...)` route; a 139-byte file route keeps its NUL.

## Routes tried and closed

- **Lpps to the GOT** (`0x804b1f0..b20c`): the store `**lpp = &buf` corrupts
  `exit`'s resolution data (or goes through `strcpy`, which writes `&buf`
  = 0xff..ff around and faults on it), and the frame we return into via
  `exit(0)` is not the one a shell `exit` builds.
- **`lpp` to 0x08048000 / 0x08048015** (mapping start, ELF header): the point
  is read-only (or the dword at 0x8048015 is 0xb8), so the `**lpp` store
  faults.
- **Any `0x0804xxxx` as `lpp`**: nothing else in that range is mapped in this
  non-PIE process.
- **Session-side frame editing** (`/proc/pid/mem`): the syscall interface
  refuses the 32-bit `lseek`/`write` pairs; `python3` is a 64-bit binary in
  a session that has no 32-bit interpreter that can use `lseek64`.
- **Session channel**: programs started through the channel never appear in
  `/proc` (`ps` shows only the ssh session itself), so a live address is not
  observable from inside, and exit codes of channel children are masked.
  Plain ssh (a command string, no pipe into python) runs on the real host
  and shows the real signals.

## Open leads

1. The 132/133 freeze gives a process that is alive, blocked on its stdin,
   with the saved return address (`buf+144`) already ours: argv[1][144..147]
   is the four bytes that become the return value of `main`.  A helper that
   forks and holds a pipe open later has to hold that call to `main` for
   long enough to either get a ptrace attach (blocked by yama `1` for
   non-ancestors, and no 32-bit ptrace front-end exists in the session), or
   to hand over a frame that is actually valid at that address.
2. The freeze itself must be explained before it can be relied on: nothing
   in `main` reads stdin after the check fails, so an out-of-process reader
   must be draining the con terminal.

## Files

- `main.dis` — live `main` disassembly; `relocs.txt` — GOT relocations and
  dynamic symbols.
- `sshraw.py` — run a command string as vortex3 over plain ssh (argv list,
  no quoting).
- `lowhost.py` / `build.py` / `l3.c` — the earlier two-trap low-host draft,
  kept for the record; the address assumptions in them predate the live
  binary analysis above.