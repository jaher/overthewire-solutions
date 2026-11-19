#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ptrace.h>
#include <sys/prctl.h>
#include <sys/wait.h>
#include <errno.h>
/* ptrace13: test whether a dumpable=0 process can be ptraced without
   CAP_SYS_PTRACE - even by the same uid.  The child sets PR_SET_DUMPABLE(0)
   and loops; the parent PTRACE_ATTACHes and reports the errno.  Then the
   child resets dumpable to 1 and the parent attaches again: the control. */
int main(void) {
    pid_t pid = fork();
    if (pid == 0) {
        prctl(PR_SET_DUMPABLE, 0);
        for (;;) pause();
    }
    sleep(1);                        /* let the child start */
    int r = ptrace(PTRACE_ATTACH, pid, 0, 0);
    printf("attach to dumpable=0 (same uid): rc=%d errno=%s\n",
           r, strerror(errno));
    if (r == 0) ptrace(PTRACE_DETACH, pid, 0, 0);
    kill(pid, 9);
    waitpid(pid, 0, 0);

    /* control: the same child shape with dumpable=1 */
    pid = fork();
    if (pid == 0) {
        prctl(PR_SET_DUMPABLE, 1);
        for (;;) pause();
    }
    sleep(1);
    errno = 0;
    r = ptrace(PTRACE_ATTACH, pid, 0, 0);
    printf("attach to dumpable=1 (same uid): rc=%d errno=%s\n",
           r, strerror(errno));
    if (r == 0) ptrace(PTRACE_DETACH, pid, 0, 0);
    kill(pid, 9);
    waitpid(pid, 0, 0);

    /* cross-uid control: a dumpable=1 process owned by a different
       uid cannot be ptraced (the uid rule) - attach from the parent
       to a child that setuid(0)-style dropped... the parent cannot
       create a different-uid child without setuid; skip: the uid
       rule is known. */
    return 0;
}
