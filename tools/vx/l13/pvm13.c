#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/uio.h>
#include <fcntl.h>
#include <errno.h>
#include <signal.h>
#include <sys/wait.h>
/* pvm13: test process_vm_readv/writev and /proc/<pid>/mem against a
   parked setuid child (the L12 level parked in safecode's loop).
   Same posture as the ptrace test: the child is setuid (fsuid 5012),
   the parent (vortex13) attempts the access. */
int main(int argc, char **argv) {
    static char buf[16384];
    FILE *f = fopen(argv[1], "r");
    if (!f) return 2;
    size_t n = fread(buf, 1, sizeof buf - 1, f);
    fclose(f);
    buf[n] = 0;
    pid_t pid = fork();
    if (pid == 0) {
        sleep(1);
        char *av[] = { "/vortex/vortex12", buf, 0 };
        execv("/vortex/vortex12", av);
        _exit(127);
    }
    sleep(3);                        /* the level parks */
    /* process_vm_readv: read the parking loop's code area */
    char rbuf[16];
    struct iovec local = { rbuf, sizeof rbuf };
    struct iovec remote = { (void *)0x08049260, sizeof rbuf };
    errno = 0;
    ssize_t r = process_vm_readv(pid, &local, 1, &remote, 1, 0);
    printf("process_vm_readv: %zd errno=%s\n", r, strerror(errno));
    /* process_vm_writev: write 4 bytes to the .bss scratch */
    char wbuf[4] = { 0x41, 0x41, 0x41, 0x41 };
    struct iovec l2 = { wbuf, 4 };
    struct iovec r2 = { (void *)0x0804c028, 4 };
    errno = 0;
    r = process_vm_writev(pid, &l2, 1, &r2, 1, 0);
    printf("process_vm_writev: %zd errno=%s\n", r, strerror(errno));
    /* /proc/<pid>/mem write */
    char mpath[64];
    snprintf(mpath, sizeof mpath, "/proc/%d/mem", pid);
    errno = 0;
    int fd = open(mpath, O_RDWR);
    printf("/proc/%d/mem open O_RDWR: %d errno=%s\n", pid, fd, strerror(errno));
    if (fd >= 0) {
        errno = 0;
        ssize_t w = pwrite(fd, wbuf, 4, (off_t)0x0804c028);
        printf("  pwrite: %zd errno=%s\n", w, strerror(errno));
        close(fd);
    }
    kill(pid, 9);
    waitpid(pid, 0, 0);
    return 0;
}
