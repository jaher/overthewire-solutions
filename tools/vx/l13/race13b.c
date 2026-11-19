#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <errno.h>
#include <signal.h>
/* race13b: the decisive post-exec attach test.  The child sleeps 2s
   PRE-exec (so the parent's attach cannot land pre-exec), then execs
   the L13 level.  The parent attaches after the exec (a 3s sleep > 2s)
   and records the errno.  The level may have already exited at the
   argc gate - the attach then reports ESRCH (process gone), which is
   itself the datum: no attach can land between exec and exit. */
int main(void) {
    pid_t pid = fork();
    if (pid == 0) {
        sleep(2);                    /* pre-exec window: the parent
                                        attaches AFTER this */
        char *av[2] = { NULL, NULL };
        char *ev[1] = { NULL };
        execv("/vortex/vortex13", av);
        _exit(127);
    }
    sleep(3);                        /* > the child's 2s: post-exec */
    errno = 0;
    int r = ptrace(PTRACE_ATTACH, pid, 0, 0);
    printf("post-exec attach: rc=%d errno=%s\n", r, strerror(errno));
    if (r == 0) { ptrace(PTRACE_DETACH, pid, 0, 0); kill(pid, 9); }
    else kill(pid, 9);
    int st;
    waitpid(pid, &st, 0);
    return 0;
}
