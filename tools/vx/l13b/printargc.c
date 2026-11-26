#include <stdio.h>
int main(int argc, char **argv, char **envp) {
    printf("argc=%d argv0=%s\n", argc, argc > 0 ? argv[0] : "(none)");
    return 0;
}
