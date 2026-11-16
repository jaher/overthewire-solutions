#include <unistd.h>
#include <stdio.h>
int main(int c, char **v){ static char buf[8192]; FILE *f=fopen(v[1],"rb");
 size_t n=fread(buf,1,sizeof buf-1,f); fclose(f); buf[n]=0;
 char *a[]={"/vortex/vortex8", buf, 0}; execv(a[0],a); return 51; }
