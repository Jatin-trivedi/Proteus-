import random
import hashlib
import base64
import ctypes

class DynamicAPIResolver:
    """
    Dynamically resolve and call APIs at runtime
    to avoid static import detection
    """
    
    def __init__(self):
        self.api_cache = {}
        self.resolved_api = {}
    
    def resolve_function(self, dll: str, function: str) -> callable:
        """
        Resolve a function dynamically
        """
        key = f"{dll}:{function}"
        
        if key in self.resolved_api:
            return self.resolved_api[key]
        
        try:
            # Load the DLL
            lib = ctypes.WinDLL(dll) if ctypes.windll else ctypes.CDLL(dll)
            
            # Get the function
            func = getattr(lib, function)
            
            # Cache it
            self.resolved_api[key] = func
            
            return func
        except:
            return None
    
    def call_api(self, dll: str, function: str, *args) -> any:
        """Call an API dynamically"""
        func = self.resolve_function(dll, function)
        if func:
            return func(*args)
        return None
    
    def generate_api_resolver_code(self, api_list: list) -> str:
        """Generate code for dynamic API resolution"""
        api_names = [
            f"'{api['dll']}','{api['function']}'"
            for api in api_list
        ]
        
        # Randomize function names
        resolver_name = f"_resolve_{random.randint(1000,9999)}"
        
        return f'''
# Dynamic API Resolver
def {resolver_name}(dll_name, func_name):
    import ctypes
    import hashlib
    
    # Obfuscated API cache
    cache = {{}}
    
    # Check if already resolved
    key = dll_name + ":" + func_name
    if key in cache:
        return cache[key]
    
    # Load library
    try:
        if dll_name.endswith('.dll'):
            lib = ctypes.WinDLL(dll_name)
        else:
            lib = ctypes.windll[dll_name]
        
        # Get function
        func = getattr(lib, func_name)
        cache[key] = func
        return func
    except:
        return None

# Pre-resolve common APIs
_apis = [
    ({api_list[0]['dll']}, {api_list[0]['function']}) if len({api_list}) > 0 else None,
]
_resolved = [None if _apis[0] is None else {resolver_name}(_apis[0][0], _apis[0][1])]

def {resolver_name}_call(dll, func, *args):
    resolved = {resolver_name}(dll, func)
    if resolved:
        return resolved(*args)
    return None
'''