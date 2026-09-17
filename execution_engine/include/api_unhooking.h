/* ============================================================================
 * Proteus- Execution Engine -- api_unhooking.h
 * API unhooking and telemetry bypass interface.
 * ============================================================================ */
#ifndef API_UNHOOKING_H
#define API_UNHOOKING_H

/* Disables or neutralizes telemetry hooks for the current platform.
 * Returns JOCKEY_ERR_OK on success, otherwise a negative error code.
 */
int bypass_telemetry(void);

/* Restores a module image to a clean, unhooked state if possible.
 * Parameters: module_name identifies the module to repair.
 * Returns JOCKEY_ERR_OK on success, otherwise a negative error code.
 */
int unhook_module(const char* module_name);

#endif
