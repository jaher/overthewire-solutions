#include <stdio.h>
#include <stdlib.h>
/* helper - pin the stack layout: prints the address of a main local
   (the same prologue as maze2: ebp-derived) and the P env value's
   address.  Run with the same env/argv shape as maze2. */
int main(int argc, char **argv) {
    char local[12];
    char *p = getenv("P");
    printf("local=%p P=%p\n", (void *)local, (void *)p);
    return 0;
}
