/* ============================================================================
 * jockey_abi.h ? ABI version contract between libjockey and its callers.
 *
 * Bump JOCKEY_ABI_VERSION any time a struct layout, enum value, or exported
 * function signature changes. The Go bridge checks this at runtime and fails
 * closed on mismatch. This prevents the class of bug where an agent built
 * against an old library links to a new one (or vice versa).
 * ============================================================================ */
#ifndef JOCKEY_ABI_H
#define JOCKEY_ABI_H

#define JOCKEY_ABI_VERSION 1u

#ifdef __cplusplus
extern "C" {
#endif

/* Returns JOCKEY_ABI_VERSION. Callers compare at startup. */
unsigned int jockey_abi_version(void);

#ifdef __cplusplus
}
#endif

#endif
