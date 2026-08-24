"""
Type signatures for JOCKY built-in functions.
Used by the compiler for type checking and code generation.
"""

BUILTIN_SIGNATURES = {
    # Windows Registry
    "collect_registry": {
        "return_type": "string",
        "parameters": ["string"],
        "description": "Collect registry key values"
    },
    
    # File System
    "collect_file": {
        "return_type": "string",
        "parameters": ["string"],
        "description": "Read file contents"
    },
    
    # Network
    "scan_network": {
        "return_type": "string",
        "parameters": [],
        "description": "Scan network interfaces"
    },
    
    # Processes
    "get_processes": {
        "return_type": "string",
        "parameters": [],
        "description": "Get running processes"
    },
    
    # System Info
    "get_system_info": {
        "return_type": "string",
        "parameters": [],
        "description": "Get system information"
    },
    
    # Packet Capture
    "capture_packets": {
        "return_type": "string",
        "parameters": ["string"],
        "description": "Capture network packets on interface"
    },
    
    # Utilities
    "pack": {
        "return_type": "string",
        "parameters": ["any"],
        "description": "Pack multiple values into a result"
    }
}