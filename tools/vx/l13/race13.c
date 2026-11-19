#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <errno.h>
#include <fcntl.h>
/* race13: measure whether PTRACE_ATTACH can land between the L13
   level's exec and its exit at the argc gate.  Spawns the level with
   argv={NULL} (an empty-argv exec), attaches in a tight loop, records
   whether any attach succeeds (it should NEVER: dumpable=0 blocks the
   parent too) and how many runs exit. */
int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: race13 <stdin-file>\n"); return 2; }
    int in = open(argv[1], O_RDONLY);
    char tmp[128];
    snprintf(tmp, sizeof tmp, "/tmp/vx13p/stdin.%d", getpid());
    int out = open(tmp, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    char b[256];
    ssize_t n = read(in, b, sizeof b);
    write(out, b, n);
    close(out);
    close(in);
    int tries = 0, attached = 0, exits = 0, eperm = 0;
    for (int run = 0; run < 20; run++) {
        pid_t pid = fork();
        if (pid == 0) {
            int i2 = open(tmp, O_RDONLY);
            dup2(i2, 0);
            close(i2);
            char *av[2] = { NULL, NULL };
            char *ev[1] = { NULL };
            execv("/vortex/vortex13", av);
            _exit(127);
        }
        tries++;
        /* tight attach loop while the level lives */
        for (;;) {
            errno = 0;
            int r = ptrace(PTRACE_ATTACH, pid, 0, 0);
            if (r == 0) {
                attached++;
                ptrace(PTRACE_DETACH, pid, 0, 0);
                break;
            }
            if (errno == EPERM) eperm++;
            int st;
            pid_t w = waitpid(pid, &st, WNOHANG);
            if (w == pid) { exits++; break; }
            if (w < 0) break;
        }
    }
    unlink(tmp);
    printf("spawns=%d attached=%d exits=%d eperm=%d\n",
           tries, attached, exits, eperm);
    return 0;
}
