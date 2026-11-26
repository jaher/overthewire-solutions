/* empty-argv exec of the REAL level binary, for strace */
#include <unistd.h>
#include <syscall.h>
#include <stdio.h>
int main(void) {
    char *argv[] = { NULL };
    char *envp[] = { NULL };
    syscall(SYS_execve, "/vortex/vortex13", argv, envp);
    printf("execve returned (failed)\n");
    return 0;
}
