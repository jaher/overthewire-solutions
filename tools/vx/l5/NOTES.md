# Vortex L5 — solution notes (solved 2026-11-16)

## The program (live binary, verified 2026-11-16)

`/vortex/vortex5`, mode 4750, setuid vortex6, group vortex5, 15428 bytes.
It is the published source (overthewire.org vortex5.c, "A tribute to arc :)"):
glibc's MD5 implementation (Colin Plumb) plus:

```c
x = getpass("Password: ");
printf("%c:%02x\n", x[strlen(x)-1], x[strlen(x)-1]);
MD5Init(&a);
MD5Update(&a, x, strlen(x));
MD5Final(buf, &a);
if (memcmp(buf, "\x15\x5f\xb9\x5d\x04\x28\x7b\x75\x7c\x99\x6d\x77\xb5\xea\x51\xf7", 16) == 0) {
    printf("You got the right password, congrats!\n");
    setresgid(getegid(), getegid(), getegid());
    setresuid(geteuid(), geteuid(), geteuid());
    system("/bin/sh");
}
```

## Measured live

- With no input it prints `:00` — `strlen(x) == 0`, so `x[-1]` reads the byte
  before getpass's static buffer.  The empty/leading-NUL password gives
  `MD5("") = d41d8cd9...`, not the target.
- The echoed pair (`t:74` for "test") is the input's last char and its code:
  the prompt's echo is off but the printf leaks the last char.

## The solution: crack the MD5 preimage

The target hash `155fb95d04287b757c996d77b5ea51f7` is the MD5 of the
password itself (no newline — getpass strips it).  All the exploitation
angles die: the getpass buffer truncates long input (the echoed last char
stays `'A'` from length 8 to 50000), `MD5("")` is not the target, and no
static-buffer leak reaches the digest.  So the intended solve is the
preimage crack.

- rockyou (14M words), with/without a newline, with mangling rules
  (caps, leet, suffixes/prefixes): **not found**.
- Brute force over the alphanumeric space finds it at length 5:
  **`rlTf6`** — `MD5("rlTf6") = 155fb95d04287b757c996d77b5ea51f7`.
- The parallel cracker (`tools/vx/l5/crack5.py`) forks 8 children over
  the 62^5 space, each checking one chunk of first letters via
  `os.fork` + `os.pipe` (multiprocessing's Pool needs POSIX semaphores,
  which the target's /dev/shm does not provide).

## Verification

- `/vortex/vortex5` with `rlTf6`: prints `6:36`, then
  `You got the right password, congrats!` and spawns `/bin/sh` with
  euid=vortex6 (`uid=5006(vortex6)`).
- `cat /etc/vortex_pass/vortex6` from that shell: `o5kBPzSFM`.
- Login as vortex6 with `o5kBPzSFM` verified (`uid=5006`).

## Password for vortex6

`o5kBPzSFM`

## Files

- `crack5.py` — the fork-based parallel MD5 cracker.
- The recording: `recordings/vortex/L5.cast`.
