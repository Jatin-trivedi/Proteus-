/* ============================================================================
 * Proteus- Execution Engine -- byovd.h
 * Bring Your Own Vulnerable Driver interface.
 * ============================================================================ */
#ifndef BYOVD_H
#define BYOVD_H

#include <stddef.h>
#include <stdint.h>

/* Loads a vulnerable driver from the provided file path.
 * Returns JOCKEY_ERR_OK or a negative error code.
 */
int load_byovd(const char* driver_path);

/* Unloads a previously loaded vulnerable driver.
 * Returns JOCKEY_ERR_OK or negative error code.
 */
int unload_byovd(const char* driver_name);

/* Disables EDR callback registration through the platform driver path.
 * Returns JOCKEY_ERR_OK or negative error code.
 */
int disable_edr_callbacks(void);

/* Kernel memory read/write */
int read_kernel_memory(uintptr_t address, void* buffer, size_t size);
int write_kernel_memory(uintptr_t address, const void* buffer, size_t size);

#endif
