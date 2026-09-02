BUILTIN_SIGNATURES = {
    "collect_registry": {
        "return_type": "string",
        "parameters": ["string"],
        "description": "Collect registry key values"
    },
    "get_processes": {
        "return_type": "string",
        "parameters": [],
        "description": "Get running processes"
    },
    "get_system_info": {
        "return_type": "string",
        "parameters": [],
        "description": "Get system information"
    },
    "scan_network": {
        "return_type": "string",
        "parameters": [],
        "description": "Scan network interfaces"
    },
    "get_open_windows": {
        "return_type": "string",
        "parameters": [],
        "description": "Enumerate open application windows and browser tabs"
    },
    "pack": {
        "return_type": "string",
        "parameters": ["any"],
        "description": "Pack multiple values into a result"
    },
    "print": {
        "return_type": "void",
        "parameters": ["string"],
        "description": "Print to console"
    }
}