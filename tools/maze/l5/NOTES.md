# Maze L5 — solved (2026-11-23)

## The program (live binary, md5 9c846f4312464a849f8a899c6d8ccc98)

`/maze/maze5`, mode 4750, setuid **maze6**, group maze5, 14940 bytes, ELF
32-bit i386 with debug_info, not stripped. Imports: printf, scanf("%8s"),
puts, system("/bin/sh"), setreuid, strlen, ptrace, geteuid.

main (0x80492c8):

```c
char user[9];   /* ebp-0x1a */
char key[9];    /* ebp-0x11 */
puts("X---------------");        /* 0x804a008 */
printf(" Username: ");
scanf("%8s", user);              /* 0x804a026 = "%8s" */
printf("     Key: ");
scanf("%8s", key);
if (strlen(user) != 8 || strlen(key) != 8) { puts("Wrong length you!"); exit(-1); }
if (ptrace(0,0,0,0) != 0)  { puts("\nnahnah..."); return 0; }   /* anti-debug */
if (foo(user, key)) {
    puts("\nYeh, here's your shell");
    setreuid(geteuid(), geteuid());      /* both args = euid = maze6 */
    system("/bin/sh");
} else puts("\nNah, wrong.");
```

foo (0x80491f6) — the check:

```c
int foo(char *user /*ebp+8*/, char *key /*ebp+0xc*/) {
    char dec[8];                        /* ebp-0xd */
    *(int*)&dec[0] = 0x6e697270;        /* "prin" */
    *(int*)&dec[4] = 0x6c6f6c74;        /* "tlol" */
    dec[8] = 0;                         /* template T = "printlol" */
    for (i = 0; i < strlen(user); i++) {
        int c = (signed char)user[i] - 'A';          /* ebp-0x14 */
        dec[i] = dec[i] - (2*i + c);                 /* byte arithmetic, wraps */
    }
    for (i = strlen(user) - 1; i >= 0; i--) {        /* reverse scan */
        if (dec[i] == key[i]) continue;
        return 0;
    }
    return 1;                           /* i wrapped to -1: eax=1 at 0x80492b0 */
}
```

(the reverse-loop exit at 0x8049280 jumps to the return-1 epilogue with eax
carrying the decremented index; only i = -1 reaches `mov eax,1`.)

## Solving the equation

The forward pass computes `dec[i] = T[i] - (2i + user[i] - 'A')` (T =
"printlol", byte arithmetic mod 256); the reverse scan requires
`dec[i] == key[i]`. So for i = 0..7:

```
key[i] = T[i] - 2i - (user[i] - 'A')   (mod 256)
```

`%8s` never writes a NUL, so user must be exactly 8 chars (the 9th stack
byte reads 0 on the live frames — verified by the "Wrong length" test).

Free choice of user; take user = "AAAAAAAA" (c = 0 for every i):

| i | T[i] | key[i] = T[i]-2i mod 256 |
|---|------|--------------------------|
| 0 | p(112) | 112 'p' |
| 1 | r(114) | 112 'p' |
| 2 | i(105) | 101 'e' |
| 3 | n(110) | 104 'h' |
| 4 | t(116) | 108 'l' |
| 5 | l(108) |  98 'b' |
| 6 | o(111) |  99 'c' |
| 7 | l(108) |  94 '^' |

key = **"ppehlbc^"** (70 70 65 68 6c 62 63 5e). My first hand-computed
attempt ("pepglbYR") had arithmetic slips in i=3..7 — recomputing in python
(`tools/maze/l5/solve.py`) gave the correct bytes.

## Result (live)

The spawned shell ignores piped stdin (it reads the tty), so the level was
run over `ssh -tt` with the commands pre-fed:

```
$ ssh -tt -p 2225 maze5@... 
maze5@gibson:~$ /maze/maze5
 Username: AAAAAAAA
     Key: ppehlbc^

Yeh, here's your shell
$ id
uid=15006(maze6) gid=15005(maze5) groups=15005(maze5)
$ cat /etc/maze_pass/maze6
dXEKrdYgQR
```

(setreuid(euid, euid) fixes BOTH uids to maze6 — `id` shows uid=15006,
gid stays 15005. Under strace the ptrace(TRACEME) check trips and prints
"nahnah..." — debug the static copy instead.)

Password `dXEKrdYgQR` verified by ssh login as maze6 (uid=15006, cat
matches).

## Files

- `maze5` — the live binary copy (md5 above).
- `solve.py` — the key derivation: key[i] = T[i] - 2i - (user[i]-'A') mod 256.
- `NOTES.md` — this file.
