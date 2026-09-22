/* ============================================================================
 * Jockey's Execution Engine -- syscalls.h
 *
 * Linux syscall numbers only.
 *
 * Windows: dynamic NT resolution via GetProcAddress in pal_win.c bypasses
 * static IAT signatures. True indirect syscalls (Halo's Gate + ntdll
 * syscall;ret gadget) are a Phase 2 upgrade — see README roadmap.
 * ============================================================================ */
#ifndef SYSCALLS_H
#define SYSCALLS_H

#ifdef __linux__

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

int syscall_invoke(int number, ...);

#ifdef __cplusplus
}
#endif

#endif /* __linux__ */
#endif /* SYSCALLS_H */