/* argv = NULL pointer entirely (not even {NULL}) */
#include <unistd.h>
#include <syscall.h>
#include <stdio.h>
int main(void) {
    long r = syscall(SYS_execve, "/tmp/vx13b/printargc", (char**)0, (char**)0);
    printf("execve(NULL argv) returned %ld\n", r);
    return 0;
}
