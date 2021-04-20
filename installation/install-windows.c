#include <stdio.h>
#include <string.h>
#include <limits.h>
#include <unistd.h>
#include <stdlib.h>
int system(const char *command);

int main(int argc, char **argv)
{
    system("python3 install.py --phase install_local");
    system("activate DeepDockingLocal");
    system("python3 install.py --phase install_remote");
    return 0;
}
