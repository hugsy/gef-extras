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
    void *r = malloc(0x28);
    void *q = malloc(0x64);

    puts("Much space, so heap!");
    fflush(stdout);

    DebugBreak();
    return 0;
}
