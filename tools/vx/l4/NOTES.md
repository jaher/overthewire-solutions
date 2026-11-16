# Vortex L4 — solution notes (solved 2026-11-16)

## The program (live binary, verified 2026-11-16)

`/vortex/vortex4`, mode 4750, setuid vortex5, group vortex4, 14844 bytes,
md5 `c77d90d5aefe8dc716e341bb518798b4` (a copy taken with mktemp -d as
vortex4).  It is the published source (overthewire.org/wargames/vortex/
vortex4.c, "andrewg, original author was zen-parse"):

```c
int main(int argc, char **argv) {
    if (argc) exit(0);
    printf(argv[3]);
    exit(EXIT_FAILURE);
}
```

The live build adds the 2013 fix: `argc==1` with `argv[0][0]==0` also
passes.  So `argc==1, argv[0]=""` reaches `printf(*(argv+12))`, and with a
one-entry argv, `argv+12` is `envp[1]`: **the format string is the second
environment variable**.  Confirmed live: env `["PADPAD","AAA=%p..."]` →
`printf` prints the second var's value with conversions applied.

## Why the usual routes die

- `.got.plt` (`0x804c000`) is writable (no BIND_NOW), but no vararg slot
  points into it.
- The GNU_RELRO segment `0x804bf00..0x804c000` covers `.init_array`,
  `.fini_array`, `.dynamic`, `.got` — all read-only at runtime.  A `%n`
  through slot 6/27 (0x804bf04, `.dynamic`) or slot 19 (0x0804908d, `.text`)
  segfaults (measured).
- The stack-pointer slots (9/13/18 = `&argc`, 14 = `&envp[0]`, 5/122-126 =
  frame cells) all write to cells nothing reads after printf.  Measured:
  `%9$n`, `%13$hn`, `%14$hn`, `%18$hn` all change nothing (rc=0).
- No vararg points into the env string area, so the classic
  "addresses in the format string" trick needs the LONG-range window.

## The route that works

printf's varargs walk **up** the stack past the initial block (argc, argv,
envp, auxv) into the strings area — including into the format string's own
bytes.  Verified by marker probes: with the env `["PADPAD", fmt]`, a dword
embedded in `fmt` is read back as a vararg at slot ≈123-126 (the exact slot
shifts with the format length; measured per length).

The exploit (121-byte format string in `envp[1]`):

1. `'XXX' + <addr1> + <addr2> + 'YYY'` — the two raw addresses of
   exit's GOT slot (`0x0804c008`) and its high half (`0x0804c00a`),
   positioned so the vararg boundary lands on them exactly (probed:
   at 121 total bytes the marker dwords are read by slots 125/126).
2. `%057229c%125$hn` — prints 57246 chars total; `%125$hn` writes
   `0xDF9E` (the low half of the shellcode address) into `0x0804c008`.
3. `%073825c%126$hn` — cumulative 131071 = `0x1FFFF`; writes `0xFFFF`
   into `0x0804c00a`.
4. exit's GOT slot now holds `0xFFFFDF9E` = the shellcode address
   (fmt_addr 0xFFFFDF6A + 52).
5. `exit(0)` → `jmp *0x804c008` → the 69-byte shellcode executes on the
   RWE stack (`readelf -l`: `GNU_STACK ... RWE`) with euid vortex5, reads
   `/etc/vortex_pass/vortex5` and prints it.

The shellcode address is deterministic: ASLR off (the OTW MOTD says so),
the env layout fixed, `fmt_addr` measured via an envp-pointer probe
(slot 63 held `0xFFFFDF6A` = envp[1] = the format string).

## Measured details

- The slot↔address mapping shifts with the format length; the probe used
  the same-length skeleton (`'XXXXMMMMNNNNYY' + conv + sled + sc`, 121
  bytes) and swept slot numbers 110..130; N=124 read the `MNNN` boundary,
  N=125/126 the embedded addresses at fmt+6/fmt+10.
- Widths are zero-padded to 5 digits so any count change keeps the format
  length fixed.
- The shellcode is the L3 69-byte open/read/write with `'5xet'` pushed
  instead of `'4xet'`; NUL-free (checked with `xxd | fold -w2`).
- The password file is 10 bytes: `uwaRhgNq1\n` (9 chars + newline).  The
  exploit prints the raw content; the login password is the 9 chars.

## Password for vortex5

`uwaRhgNq1` — printed by the shellcode from `/etc/vortex_pass/vortex5`
and verified by logging in as vortex5 (`uid=5005`).

## Files

- `sc.asm` — the 69-byte shellcode (nasm).
- `ex6.py` — the ctypes execve runner (argv `[b""]`, env PADPAD + fmt).
- `gen.py` — builds `fmt.bin` (121 bytes).
- The recording: `recordings/vortex/L4.cast`.
