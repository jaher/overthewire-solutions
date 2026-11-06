# Vortex L3 — where the work stands

## The program

`/vortex/vortex3` is the 0xbadc0ded #02 source compiled for i386 (Ubuntu
gcc 15.2):

```c
int main(int argc, char **argv) {
    unsigned long val = 31337;
    unsigned long *lp = &val;
    unsigned long **lpp = &lp, *tmp;
    char buf[128];
    if (argc != 2) exit(1);
    strcpy(buf, argv[1]);
    if (((unsigned long) lpp & 0xffff0000) != 0x08040000) exit(2);
    tmp = *lpp;
    **lpp = (unsigned long) &buf;
    exit(0);
}
```

The frame (from `objdump -d`): return address at `buf+128`, saved `ebp` at
`buf+132`, `lpp` at `ebp-0xc`, `lp` at `ebp-0x10`; the check is
`(lpp & 0xffff0000) == 0x08040000` (`mov -0xc(%ebp),%eax; mov $0,%ax;
cmp $0x08040000,%eax`).  The last store is `**lpp = &buf`.  `vortex3-hard`
adds `*lpp = tmp` after it and nothing else.

## Live behaviour

- `vortex3 AAAA` → exit 0; `vortex3` → exit 1; length 129 → 0, 130 → exit 2
  (overwritten low `lpp` no longer passes the check); length 132 → SIGSEGV
  (saved `ebp` destroyed before `lpp` is read).
- The intended pivot is to have `lpp` point at a constant address in
  0x0804xxxx; its value then becomes `&buf` and walking it (`**lpp`, the
  saved `tmp`, later bytes) reads/writes the stack, including the return
  address and the password-mapped process image.

## What the session allows

Checked one operation at a time (tools/vx/l3/lowhost.py and the probes under
/tmp, results in OTW-PROGRESS.md): file writes, fork/wait, exec of children,
signals, `mmap` and `mprotect` all work.  Two things do not show up through
the channel: exit codes of processes only the channel started are recorded
as 0/2, and an instruction trap from code placed by the session is reported
as a crash without its output.  The trap itself is still the intended way to
get the crypt-net/registers op reached from the copied exit frame.

## The route being built

1. The exit frame copies `eip = 0x0804b0dc` (exit@plt tail: `mov eax,[ebx];
   add eax,edi; jmp eax`, `ebx = 0x0804b00c`, `edi = 0x8ca`) with the
   register file the kernel saved on the child's stack.
2. The argument carries the chain `ebx` → mailbox (`A`; offset 0x64 = `d`) →
   payload (`B`; next letter `e`) → `call [0x0804b0dc]`: the frame's saved
   return address points at the trap that consumes the saved registers, then
   continues at `LowHost+0x200` (= `0x08048200`) in the next process.
3. `LowHost` body at 0x08048000: `sti; mov eax,20; mov ebx,9; int 0x80`
   writes the image modifier at `0x0804b000`, then exits 1 cleanly.
4. The script part at `0x08049100` asks for the two traps and reads
   `/etc/vortex_pass/vortex4` in the state that runs the next process.

`lowhost.py` holds the assembled program; it needs a run of the full
argument to confirm each step.