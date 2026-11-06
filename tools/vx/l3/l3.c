#include <stdio.h>
#include <string.h>
#include <stdlib.h>
int main(int argc, char **argv) {
    unsigned long val = 31337;
    unsigned long *lp = &val;
    unsigned long **lpp = &lp, *tmp;
    char buf[128];
    if (argc != 2) exit(1);
    strcpy(buf, argv[1]);
    if (((unsigned long) lpp & 0xffff0000) != 0x08040000) exit(2);
    tmp = *lpp;
    **lpp = (unsigned long) &buf;
    printf("%lx %lx\n", (unsigned long)lp, (unsigned long)&buf);
    exit(0);
}
