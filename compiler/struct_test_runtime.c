
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <psapi.h>
#include <tlhelp32.h>

extern char* struct_test();

char* jocky_int_to_str(long long val) {
    static char buf[64];
    snprintf(buf, sizeof(buf), "%lld", val);
    return buf;
}

char* jocky_collect_registry(const char* hive) {
    HKEY hKey;
    char* result = malloc(4096);
    result[0] = '\0';
    char hive_copy[256];
    strcpy(hive_copy, hive);
    char* path = strchr(hive_copy, '\\');
    if (path) { *path = '\0'; path++; }
    HKEY hRoot;
    if (strcmp(hive_copy, "HKLM") == 0) hRoot = HKEY_LOCAL_MACHINE;
    else if (strcmp(hive_copy, "HKCU") == 0) hRoot = HKEY_CURRENT_USER;
    else if (strcmp(hive_copy, "HKCR") == 0) hRoot = HKEY_CLASSES_ROOT;
    else {
        sprintf(result, "{\"error\":\"Unknown hive: %s\"}", hive_copy);
        return result;
    }
    if (RegOpenKeyEx(hRoot, path, 0, KEY_READ, &hKey) == ERROR_SUCCESS) {
        DWORD index = 0;
        char value_name[256];
        DWORD value_name_size = 256;
        DWORD value_type;
        char value_data[1024];
        DWORD value_data_size = 1024;
        strcat(result, "{");
        while (RegEnumValue(hKey, index++, value_name, &value_name_size, 
                           NULL, &value_type, (LPBYTE)value_data, &value_data_size) == ERROR_SUCCESS) {
            if (index > 1) strcat(result, ",");
            if (value_type == REG_SZ || value_type == REG_EXPAND_SZ) {
                sprintf(result + strlen(result), "\"%s\":\"%s\"", value_name, value_data);
            } else if (value_type == REG_DWORD) {
                sprintf(result + strlen(result), "\"%s\":%d", value_name, *(DWORD*)value_data);
            }
            value_name_size = 256;
            value_data_size = 1024;
        }
        strcat(result, "}");
        RegCloseKey(hKey);
    } else {
        sprintf(result, "{\"error\":\"Failed to open key: %s\"}", path);
    }
    return result;
}

char* jocky_get_processes() {
    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnapshot == INVALID_HANDLE_VALUE) return "{\"error\":\"Failed\"}";
    PROCESSENTRY32 pe32;
    pe32.dwSize = sizeof(PROCESSENTRY32);
    char* result = malloc(16384);
    result[0] = '\0';
    strcat(result, "[");
    int first = 1;
    if (Process32First(hSnapshot, &pe32)) {
        do {
            if (!first) strcat(result, ",");
            first = 0;
            char entry[512];
            sprintf(entry, "{\"pid\":%d,\"name\":\"%s\"}", pe32.th32ProcessID, pe32.szExeFile);
            strcat(result, entry);
        } while (Process32Next(hSnapshot, &pe32));
    }
    strcat(result, "]");
    CloseHandle(hSnapshot);
    return result;
}

char* jocky_get_system_info() {
    char* result = malloc(2048);
    result[0] = '\0';
    SYSTEM_INFO si; GetSystemInfo(&si);
    OSVERSIONINFO osvi; osvi.dwOSVersionInfoSize = sizeof(OSVERSIONINFO);
    GetVersionEx(&osvi);
    sprintf(result, "{\"os\":\"Windows\",\"version\":\"%d.%d\",\"arch\":\"x%d\",\"cores\":%d}",
            osvi.dwMajorVersion, osvi.dwMinorVersion,
            si.wProcessorArchitecture == PROCESSOR_ARCHITECTURE_AMD64 ? 64 : 32,
            si.dwNumberOfProcessors);
    return result;
}

char* jocky_scan_network() {
    char* result = malloc(4096);
    result[0] = '\0';
    FILE* fp = popen("ipconfig /all", "r");
    if (!fp) return "{\"error\":\"Failed\"}";
    char line[512];
    strcat(result, "{\"output\":\"");
    while (fgets(line, sizeof(line), fp)) {
        for (char* c = line; *c; c++) {
            if (*c == '"' || *c == '\\') strcat(result, "\\");
            if (*c == '\n') continue;
            strncat(result, c, 1);
        }
    }
    strcat(result, "\"}");
    pclose(fp);
    return result;
}

int main() {
    printf("=== JOCKY Starting ===\n");
    char* result = struct_test();
    if (result) {
        puts(result);
    }
    printf("=== JOCKY Finished ===\n");
    return 0;
}
