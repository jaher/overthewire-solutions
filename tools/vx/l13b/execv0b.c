/* argv = {"", NULL} - single empty string (what 5.18+ forces anyway) */
#include <unistd.h>
#include <syscall.h>
#include <stdio.h>
int main(void) {
    char *argv[] = { "", NULL };
    char *envp[] = { NULL };
    long r = syscall(SYS_execve, "/tmp/vx13b/printargc", argv, envp);
    printf("execve({empty}) returned %ld\n", r);
    return 0;
}
