#include <windows.h>

static int slen(const char *s) { int n = 0; while (s[n]) n++; return n; }

static DWORD resolve_temp(char *path, DWORD cap) {
    DWORD tlen = GetTempPathA(cap, path);  /* correct arg order */
    if (tlen == 0 || tlen >= cap - 32) {
        const char *fb = "C:\\Windows\\Temp\\";
        DWORD i = 0;
        while (fb[i] && i < cap - 1) { path[i] = fb[i]; i++; }
        path[i] = 0;
        tlen = i;
    }
    return tlen;
}

BOOL WINAPI DllMain(HINSTANCE hinst, DWORD reason, LPVOID reserved) {
    (void)hinst; (void)reserved;
    if (reason != DLL_PROCESS_ATTACH) return TRUE;

    char path[MAX_PATH];
    DWORD tlen = resolve_temp(path, MAX_PATH);

    const char *name = "INJ_reflective.txt";
    int k = 0;
    while (name[k] && (tlen + k) < MAX_PATH - 1) { path[tlen + k] = name[k]; k++; }
    path[tlen + k] = 0;

    HANDLE h = CreateFileA(path, GENERIC_WRITE, 0, NULL,
                           CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (h == INVALID_HANDLE_VALUE) return TRUE;

    const char *msg = "reflective DLL OK\n";
    DWORD w = 0;
    WriteFile(h, msg, slen(msg), &w, NULL);
    CloseHandle(h);
    return TRUE;
}
