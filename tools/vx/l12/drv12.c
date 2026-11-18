#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
/* drv12 - run /vortex/vortex12 with a raw-byte argv[1] read from a file
   (the payload contains binary bytes; a shell argument would mangle it) */
int main(int argc, char **argv) {
    static char buf[16384];
    FILE *f = fopen(argv[1], "r");
    if (!f) return 1;
    size_t n = fread(buf, 1, sizeof buf - 1, f);
    fclose(f);
    buf[n] = 0;
    char *av[] = { "/vortex/vortex12", buf, 0 };
    execv("/vortex/vortex12", av);
    return 1;
}
