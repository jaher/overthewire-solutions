# Maze L1 — solved (2026-11-22)

## The program (live binary, md5 b250dac8531a12793541b54f8a9993c8)

`/maze/maze1`, mode 4750, setuid maze2, group maze1, 12316 bytes, with
debug_info, not stripped.  main is 23 bytes: `puts("Hello World!\n")`.
The DT_NEEDED entries: **`./libc.so.4`** (a relative path!) and
`libc.so.6`.

## The exploit

1. Run the binary from a directory containing a planted `libc.so.4`:
   `D=$(mktemp -d); chmod 755 $D; cd $D`.
2. Two loader gotchas, both measured live:
   - the loader opens libraries with the setuid binary's **fsuid**
     (maze2), so the mktemp dir must be 755 (a 700 dir owned by maze1
     is unreadable by fsuid 5012 → "Permission denied");
   - the planted file must be a **valid 32-bit ELF shared object**
     (an empty file → "file too short"; a 64-bit build → "wrong ELF
     class: ELFCLASS64").
3. The planted `libc.so.4` (lib4.c) carries a **constructor** that
   runs at load time, before main, with the setuid binary's fsuid
   (maze2): it reads /etc/maze_pass/maze2 and prints it.

## Result

Password for maze2: **jJF6jn9qW6** — printed by the constructor and
verified by logging in as maze2 (uid=15002, cat matches).

## Files

- `lib4.c` — the planted library (the constructor).
- `maze1` — the live binary copy (md5 above).
