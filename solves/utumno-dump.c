/* dump.c -- read a process's own memory from inside that process.
 *
 * utumno0 is execute-only (---x--x---): we may run it but not open it, so
 * strings/objdump/nm/ltrace all fail with "Permission denied", and ptrace
 * cannot read it either.  But the *pages* the kernel maps for the running
 * process are readable by the process itself -- the missing permission is on
 * the file, not on the mapping.  A shared library loaded with LD_PRELOAD runs
 * inside that process, so a constructor can copy the mapped segments out.
 *
 * The binary is 32-bit, so this must be compiled with -m32; a 64-bit .so is
 * rejected by the loader ("wrong ELF class: ELFCLASS64").
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>

__attribute__((constructor)) static void dump(void)
{
    FILE *m   = fopen("/proc/self/maps", "r");
    FILE *img = fopen("image.bin", "wb");
    FILE *txt = fopen("maps.txt", "w");
    char line[512];

    if (!m || !img || !txt) return;

    while (fgets(line, sizeof line, m)) {
        unsigned long lo, hi, off;
        char perms[8], path[256] = "";

        int n = sscanf(line, "%lx-%lx %7s %lx %*s %*s %255s",
                       &lo, &hi, perms, &off, path);
        if (n < 4) continue;
        if (!strstr(path, "/utumno/utumno0")) continue;

        fputs(line, txt);
        if (!strchr(perms, 'r')) continue;   /* only segments we can read */
        fwrite((void *)lo, 1, hi - lo, img);
    }

    fclose(m);
    fclose(img);
    fclose(txt);
}
