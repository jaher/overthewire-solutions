/* execveat with AT_EMPTY_PATH on an O_RDONLY fd of the target, argv={NULL} */
#define _GNU_SOURCE
#include <unistd.h>
#include <syscall.h>
#include <fcntl.h>
#include <stdio.h>
int main(void) {
    int fd = open("/tmp/vx13b/printargc", O_RDONLY);
    char *argv[] = { NULL };
    char *envp[] = { NULL };
    long r = syscall(SYS_execveat, fd, "", argv, envp, AT_EMPTY_PATH);
    printf("execveat returned %ld\n", r);
    return 0;
}
