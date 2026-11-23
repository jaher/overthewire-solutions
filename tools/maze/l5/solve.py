#!/usr/bin/env python3
"""Maze L5 key derivation.

foo() computes:  dec[i] = "printlol"[i] - (2*i + user[i] - 'A')   (byte, mod 256)
then requires dec[i] == key[i] for i = 7..0 (reverse scan; success iff the
index wraps to -1).  Hence key[i] = T[i] - 2*i - (user[i]-'A')  (mod 256).
"""
T = b"printlol"

def key_for(user: bytes) -> bytes:
    assert len(user) == 8
    return bytes((T[i] - 2 * i - (user[i] - 65)) & 0xff for i in range(8))

if __name__ == "__main__":
    user = b"AAAAAAAA"
    k = key_for(user)
    print("user:", user.decode(), "key:", k.decode())
    # verify by replaying foo() exactly
    dec = bytearray(T)
    for i in range(8):
        dec[i] = (dec[i] - (2 * i + (user[i] - 65))) & 0xff
    assert bytes(dec) == k
    print("replay OK:", dec.hex())
