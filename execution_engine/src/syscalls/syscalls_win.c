/* ============================================================================
 * Proteus- Execution Engine -- syscalls_win.c
 * Windows direct syscall stubs (placeholder for future hardening).
 * ============================================================================ */

#include "../../include/syscalls.h"
#include "../../include/pal.h"

#ifdef _WIN32

uint32_t g_syscall_nt_open_process = 0;
uint32_t g_syscall_nt_allocate_virtual_memory = 0;
uint32_t g_syscall_nt_write_virtual_memory = 0;
uint32_t g_syscall_nt_protect_virtual_memory = 0;
uint32_t g_syscall_nt_create_thread_ex = 0;
uint32_t g_syscall_nt_close = 0;

int syscalls_init(void) {
    HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
    if (!hNtdll) return -1;

    /* Syscall numbers extracted from ntdll exports at runtime */
    /* This is a simplified stub; production would use HellsGate/HalosGate */
    g_syscall_nt_open_process = 0x26;
    g_syscall_nt_allocate_virtual_memory = 0x18;
    g_syscall_nt_write_virtual_memory = 0x3A;
    g_syscall_nt_protect_virtual_memory = 0x50;
    g_syscall_nt_create_thread_ex = 0xC1;
    g_syscall_nt_close = 0x0F;

    LOG_INFO("[+] Syscall numbers initialized (stub mode)");
    return 0;
}

int sys_nt_open_process(PHANDLE process_handle, ACCESS_MASK desired_access,
                        POBJECT_ATTRIBUTES object_attributes, PCLIENT_ID client_id) {
    (void)process_handle; (void)desired_access;
    (void)object_attributes; (void)client_id;
    return -1;
}

int sys_nt_allocate_virtual_memory(HANDLE process_handle, PVOID* base_address,
                                   ULONG_PTR zero_bits, PSIZE_T region_size,
                                   ULONG allocation_type, ULONG protect) {
    (void)process_handle; (void)base_address; (void)zero_bits;
    (void)region_size; (void)allocation_type; (void)protect;
    return -1;
}

int sys_nt_write_virtual_memory(HANDLE process_handle, PVOID base_address,
                                PVOID buffer, ULONG number_of_bytes_to_write,
                                PULONG number_of_bytes_written) {
    (void)process_handle; (void)base_address; (void)buffer;
    (void)number_of_bytes_to_write; (void)number_of_bytes_written;
    return -1;
}

#endif
