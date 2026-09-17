/* ============================================================================
 * Proteus- Execution Engine -- pal_linux.c
 * Linux Platform Abstraction Layer.
 * ============================================================================ */

#include "../../include/pal.h"
#include "../../include/byovd.h"
#include "../../include/api_unhooking.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/ptrace.h>
#include <sys/mman.h>
#include <sys/user.h>
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>

struct PalProcess {
    pid_t pid;
    int   status;
};

void pal_set_use_direct_syscalls(int flag) {
    (void)flag;
}

int pal_create_process_suspended(const char* image_path, PalProcess** out) {
    if (!image_path || !out) return JOCKEY_ERR_INVALID_PARAM;
    pid_t pid = fork();
    if (pid < 0) return JOCKEY_ERR_OS_API;
    if (pid == 0) {
        if (ptrace(PTRACE_TRACEME, 0, NULL, NULL) < 0) {
            _exit(1);
        }
        raise(SIGSTOP);
        execl(image_path, image_path, NULL);
        _exit(1);
    }
    int status;
    waitpid(pid, &status, 0);
    PalProcess* proc = (PalProcess*)calloc(1, sizeof(PalProcess));
    if (!proc) return JOCKEY_ERR_MEMORY_ALLOC;
    proc->pid = pid;
    proc->status = status;
    *out = proc;
    return JOCKEY_ERR_OK;
}

int pal_resume_process(PalProcess* proc) {
    if (!proc) return JOCKEY_ERR_INVALID_PARAM;
    if (ptrace(PTRACE_CONT, proc->pid, NULL, NULL) < 0) return JOCKEY_ERR_OS_API;
    return JOCKEY_ERR_OK;
}

int pal_terminate_process(PalProcess* proc) {
    if (!proc) return JOCKEY_ERR_INVALID_PARAM;
    kill(proc->pid, SIGKILL);
    return JOCKEY_ERR_OK;
}

int pal_wait_for_process(PalProcess* proc) {
    if (!proc) return JOCKEY_ERR_INVALID_PARAM;
    int status;
    waitpid(proc->pid, &status, 0);
    return JOCKEY_ERR_OK;
}

void pal_close_process(PalProcess* proc) {
    free(proc);
}

uint32_t pal_get_pid(PalProcess* proc) {
    if (!proc) return 0;
    return (uint32_t)proc->pid;
}

void* pal_allocate_memory_remote(PalProcess* proc, size_t size, int protection) {
    (void)proc; (void)size; (void)protection;
    return NULL;
}

int pal_write_memory_remote(PalProcess* proc, void* dest, const void* src, size_t size) {
    (void)proc; (void)dest; (void)src; (void)size;
    return JOCKEY_ERR_GENERIC;
}

int pal_read_memory_remote(PalProcess* proc, const void* src, void* dest, size_t size) {
    (void)proc; (void)src; (void)dest; (void)size;
    return JOCKEY_ERR_GENERIC;
}

int pal_protect_memory_remote(PalProcess* proc, void* addr, size_t size, int protection) {
    (void)proc; (void)addr; (void)size; (void)protection;
    return JOCKEY_ERR_GENERIC;
}

int pal_free_memory_remote(PalProcess* proc, void* addr) {
    (void)proc; (void)addr;
    return JOCKEY_ERR_GENERIC;
}

int pal_create_remote_thread(PalProcess* proc, void* start_routine, void* arg) {
    (void)proc; (void)start_routine; (void)arg;
    return JOCKEY_ERR_GENERIC;
}

int pal_get_thread_context(PalProcess* proc, void* context) {
    (void)proc; (void)context;
    return JOCKEY_ERR_GENERIC;
}

int pal_set_thread_context(PalProcess* proc, const void* context) {
    (void)proc; (void)context;
    return JOCKEY_ERR_GENERIC;
}

int pal_load_driver(const char* driver_path) {
    return load_byovd(driver_path);
}

int pal_unload_driver(const char* driver_name) {
    return unload_byovd(driver_name);
}

int pal_read_kernel_memory(uintptr_t address, void* buffer, size_t size) {
    return read_kernel_memory(address, buffer, size);
}

int pal_write_kernel_memory(uintptr_t address, const void* buffer, size_t size) {
    return write_kernel_memory(address, buffer, size);
}

int pal_unhook_module(const char* module_name) {
    return unhook_module(module_name);
}

int pal_bypass_telemetry(void) {
    return bypass_telemetry();
}

int pal_remote_dlopen(PalProcess* proc, const void* so_data, size_t so_size) {
    (void)proc; (void)so_data; (void)so_size;
    return JOCKEY_ERR_GENERIC;
}

int pal_syscall_open_process(uint32_t pid, int access, PalProcess** out) {
    (void)pid; (void)access; (void)out;
    return JOCKEY_ERR_GENERIC;
}

int pal_syscall_allocate_memory(PalProcess* proc, void** addr, size_t size, int protection) {
    (void)proc; (void)addr; (void)size; (void)protection;
    return JOCKEY_ERR_GENERIC;
}

int pal_syscall_write_memory(PalProcess* proc, void* dest, const void* src, size_t size) {
    (void)proc; (void)dest; (void)src; (void)size;
    return JOCKEY_ERR_GENERIC;
}
