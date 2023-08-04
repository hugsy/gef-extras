/**
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "utils.h"

int main(int argc, char **argv)
{
    void *p = malloc(0x64);
    (void)p;
    void *r = malloc(0x28);
    (void)r;
    void *q = malloc(0x64);
    (void)q;

    puts("Much space, so heap!");
    fflush(stdout);

    DebugBreak();
    return 0;
}
