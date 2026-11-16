/* h11.c — L11 EGG address pin.
 *
 * ASLR is off, so the kernel places the env strings identically for any
 * execve with the same total argv+envp byte lengths.  This helper is
 * invoked with the SAME two argv strings as /vortex/vortex11 (path
 * length 16+1 = 17 chars, same as the level's), so getenv("EGG")
 * reports the exact address the level's process will see.
 *
 *   gcc -m32 -o h11 h11.c
 *   EGG="$(cat egg.bin)"; ./h11 "$(cat craft.bin)" "BBBBBBBBBBBBBBB"
 */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    printf("%p\n", (void*)getenv("EGG"));
    return 0;
}
