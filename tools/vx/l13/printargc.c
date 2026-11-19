#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
/* printargc: the exec target of an empty-argv execve; prints argc. */
int main(int argc, char **argv) {
    printf("argc=%d\n", argc);
    return 0;
}
