/* ============================================================================
 * Jockey's Execution Engine -- syscalls.h
 * Syscall number definitions. Platform-specific wrappers in pal.
 * ============================================================================ */
#ifndef SYSCALLS_H
#define SYSCALLS_H

#ifdef _WIN32
#include <windows.h>
#include <winternl.h>
#endif

#define SYS_READ    0
#define SYS_WRITE   1
#define SYS_OPEN    2
#define SYS_CLOSE   3
#define SYS_MMAP    9
#define SYS_MUNMAP  11
#define SYS_EXECVE  59
#define SYS_CLONE   56
#define SYS_PTRACE  101

#ifdef __cplusplus
extern "C" {
#endif

/* Generic syscall dispatcher (platform-specific implementations) */
int syscall_invoke(int number, ...);

#ifdef _WIN32
/* Windows syscall wrappers */
int sys_nt_open_process(PHANDLE process_handle, ACCESS_MASK desired_access,
                        POBJECT_ATTRIBUTES object_attributes, PCLIENT_ID client_id);
#endif

#ifdef __cplusplus
}
#endif

#endif
