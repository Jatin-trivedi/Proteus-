#include <windows.h>

static int slen(const char *s) { int n = 0; while (s[n]) n++; return n; }

static DWORD resolve_temp(char *path, DWORD cap) {
    DWORD tlen = GetTempPathA(cap, path);
    if (tlen == 0 || tlen >= cap - 32) {
        const char *fb = "C:\\Windows\\Temp\\";
        DWORD i = 0;
        while (fb[i] && i < cap - 1) { path[i] = fb[i]; i++; }
        path[i] = 0;
        tlen = i;
    }
    return tlen;
}

static void wfile_in_temp(const char *name, const char *msg) {
    char path[MAX_PATH];
    DWORD tlen = resolve_temp(path, MAX_PATH);
    int k = 0;
    while (name[k] && (tlen + k) < MAX_PATH - 1) { path[tlen + k] = name[k]; k++; }
    path[tlen + k] = 0;

    HANDLE h = CreateFileA(path, GENERIC_WRITE, 0, NULL,
                           CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (h == INVALID_HANDLE_VALUE) return;
    DWORD w = 0;
    WriteFile(h, msg, slen(msg), &w, NULL);
    CloseHandle(h);
}

void hollow_body(void) {
    wfile_in_temp("hollow_cp1.txt",  "cp1\n");
    wfile_in_temp("INJ_hollowing.txt","hollowing OK\n");
    ExitProcess(0);
}

__attribute__((naked, used, noinline))
void shell_entry(void) {
    __asm__ volatile(
        "andq $-16, %rsp\n"
        "call hollow_body\n"
        "ud2\n"
    );
}
