/* raw-syscall execve with argv = {NULL}: the classic argc==0 attempt */
#include <unistd.h>
#include <syscall.h>
#include <stdio.h>
int main(void) {
    char *argv[] = { NULL };
    char *envp[] = { NULL };
    long r = syscall(SYS_execve, "/tmp/vx13b/printargc", argv, envp);
    printf("execve returned %ld\n", r);
    return 0;
}
