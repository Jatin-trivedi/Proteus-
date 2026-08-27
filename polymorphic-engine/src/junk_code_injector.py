"""
Junk Code Injector - Adds meaningless code to confuse analysis
"""

import random
import string
from typing import List, Dict, Any, Optional

class JunkCodeInjector:
    """Injects junk code and dead code into scripts"""
    
    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._junk_functions = []
        self._generate_junk_functions()
        
    def _generate_junk_functions(self):
        """Generate a pool of junk functions"""
        self._junk_functions = [
            self._generate_math_junk,
            self._generate_string_junk,
            self._generate_loop_junk,
            self._generate_condition_junk,
            self._generate_random_operation_junk,
        ]
        
    def inject_junk_code(self, code: str) -> str:
        """
        Inject junk code at random positions
        """
        lines = code.split('\n')
        
        # Determine injection points
        num_injections = self._rng.randint(1, 5)
        injection_points = sorted(
            self._rng.sample(range(1, len(lines)-1), min(num_injections, len(lines)-2))
        )
        
        # Inject junk at each point
        for i, point in enumerate(injection_points):
            # Generate junk block
            junk = self._generate_junk_block()
            
            # Insert before the line
            lines.insert(point + i, junk)
            
        # Add junk at the beginning
        if self._rng.random() > 0.5:
            lines.insert(0, self._generate_function_junk())
            
        # Add junk at the end
        if self._rng.random() > 0.5:
            lines.append(self._generate_function_junk())
            
        return '\n'.join(lines)
    
    def _generate_junk_block(self) -> str:
        """Generate a block of junk code"""
        lines = []
        
        # Random number of lines
        num_lines = self._rng.randint(1, 4)
        
        for _ in range(num_lines):
            # Randomly choose a junk generator
            generator = self._rng.choice(self._junk_functions)
            lines.append(generator())
            
        # Add a comment to make it look legit
        if self._rng.random() > 0.5:
            lines.insert(0, f"# {self._generate_random_comment()}")
            
        return '\n'.join(lines)
    
    def _generate_math_junk(self) -> str:
        """Generate junk math operations"""
        ops = ['+', '-', '*', '/', '%', '**']
        
        # Create a variable to store the result
        var = f"_junk_{self._rng.randint(1000,9999)}"
        
        # Build expression
        num1 = self._rng.randint(1, 1000)
        num2 = self._rng.randint(1, 1000)
        op = self._rng.choice(ops)
        
        return f"{var} = {num1} {op} {num2}"
    
    def _generate_string_junk(self) -> str:
        """Generate junk string operations"""
        # Renamed 'string' to 'junk_string' to avoid shadowing the 'string' module
        junk_string = ''.join(
            self._rng.choice(string.ascii_letters + string.digits)
            for _ in range(self._rng.randint(5, 20))
        )
        
        operations = [
            f"__import__('base64').b64encode(b'{junk_string}')",
            f"len('{junk_string}')",
            f"'{junk_string}'[::-1]",
            f"'{junk_string}'.upper()",
            f"'{junk_string}'.lower()",
        ]
        
        op = self._rng.choice(operations)
        var = f"_junk_{self._rng.randint(1000,9999)}"
        
        return f"{var} = {op}"
    
    def _generate_loop_junk(self) -> str:
        """Generate junk loops"""
        if self._rng.random() > 0.5:
            # For loop
            count = self._rng.randint(1, 5)
            return f"for _ in range({count}): pass"
        else:
            # While loop
            return f"while False: pass"
    
    def _generate_condition_junk(self) -> str:
        """Generate junk conditional"""
        var = self._rng.choice(['x', 'y', 'z', 'a', 'b', 'c'])
        
        if self._rng.random() > 0.5:
            return f"if {var} == {var}: pass"
        else:
            return f"if {var} != {var}: pass"
    
    def _generate_random_operation_junk(self) -> str:
        """Generate random operations"""
        operations = [
            f"__import__('os').path.exists('/tmp')",
            f"__import__('time').sleep(0.001)",
            f"__import__('sys').platform",
            f"__import__('hashlib').md5(b'junk').hexdigest()",
            f"__import__('random').random()",
        ]
        
        op = self._rng.choice(operations)
        var = f"_junk_{self._rng.randint(1000,9999)}"
        
        return f"{var} = {op}"
    
    def _generate_function_junk(self) -> str:
        """Generate a junk function definition"""
        func_name = f"_junk_{self._rng.randint(1000,9999)}"
        args = []
        
        # Generate random parameters
        num_args = self._rng.randint(1, 3)
        for i in range(num_args):
            args.append(f"arg{i}")
            
        # Generate body
        body_lines = []
        num_lines = self._rng.randint(1, 3)
        for _ in range(num_lines):
            generator = self._rng.choice(self._junk_functions)
            body_lines.append(f"    {generator()}")
            
        # Return something
        if self._rng.random() > 0.5:
            body_lines.append(f"    return {self._rng.randint(0, 100)}")
        else:
            body_lines.append("    pass")
            
        args_str = ', '.join(args)
        
        return f"def {func_name}({args_str}):\n" + '\n'.join(body_lines)
    
    def _generate_random_comment(self) -> str:
        """Generate a random comment"""
        comments = [
            "Optimization phase",
            "Cache cleanup",
            "Error handling",
            "Memory management",
            "Thread synchronization",
            "Logging initialization",
            "Configuration check",
            "Environment setup",
            "Resource allocation",
            "Task scheduling",
        ]
        return self._rng.choice(comments)
    
    def inject_junk_section(self, binary_data: bytes) -> bytes:
        """
        Inject junk data into a binary
        """
        # Add random data at end
        junk_size = self._rng.randint(256, 1024)
        junk_data = self._rng.getrandbits(junk_size * 8).to_bytes(junk_size, 'big')
        
        # Also add some recognizable patterns
        patterns = [
            b'DEADBEEF',
            b'0xDEADBEEF',
            f"JOCKY_{self._rng.randint(1000,9999)}".encode(),
            self._rng.getrandbits(128).to_bytes(16, 'big')
        ]
        
        for pattern in self._rng.sample(patterns, self._rng.randint(1, len(patterns))):
            junk_data += pattern
            
        return binary_data + junk_data