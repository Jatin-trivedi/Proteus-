"""
Main Obfuscator - Coordinates all polymorphic transformations
"""

import os
import random
import tempfile
import subprocess
from typing import Dict, Any, Optional, List, Tuple
import struct
import re

from .hash_generator import HashGenerator
from .variable_encryption import VariableEncryptor
from .control_flow_flattener import ControlFlowFlattener
from .import_table_obfuscator import ImportTableObfuscator
from .junk_code_injector import JunkCodeInjector

class PolymorphicObfuscator:
    """
    Master orchestrator for all polymorphic transformations
    Each execution produces a unique binary
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.hash_gen = HashGenerator(seed)
        self.var_encryptor = VariableEncryptor(seed)
        self.flow_flattener = ControlFlowFlattener(seed)
        self.import_obfuscator = ImportTableObfuscator()
        self.junk_injector = JunkCodeInjector(seed)
        self._rng = random.Random(seed)
        
    def obfuscate_script(self, script_content: str) -> Dict[str, Any]:
        """
        Apply all polymorphic transformations to a script
        Returns transformed script and metadata
        """
        # Step 1: Randomize variables and functions
        script = self._randomize_identifiers(script_content)
        
        # Step 2: Inject junk code
        script = self.junk_injector.inject_junk_code(script)
        
        # Step 3: Flatten control flow (if script has loops/conditionals)
        script = self.flow_flattener.flatten_control_flow(script)
        
        # Step 4: Encrypt string constants
        script = self.var_encryptor.encrypt_strings(script)
        
        # Step 5: Generate unique hashes
        hashes = self.hash_gen.generate_script_hash(script)
        
        # Step 6: Add unique header/footer
        script = self._add_unique_markers(script)
        
        return {
            'obfuscated_script': script,
            'hashes': hashes,
            'seed': self.hash_gen.seed,
            'transformations': self._get_transform_log()
        }
    
    def _randomize_identifiers(self, code: str) -> str:
        """
        Rename all identifiers (variables, functions, etc.)
        to random names that change every run
        """
        # Pattern to match identifiers (simplified for demo)
        # In production, you'd parse the AST properly
        identifier_pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
        
        # Keywords to preserve
        keywords = {
            'if', 'else', 'for', 'while', 'return', 'import', 'from',
            'def', 'class', 'try', 'except', 'with', 'as', 'lambda',
            'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is',
            'break', 'continue', 'raise', 'assert', 'del', 'global',
            'nonlocal', 'yield', 'await', 'async', 'pass'
        }
        
        # Builtins to preserve
        builtins = {
            'print', 'len', 'str', 'int', 'float', 'list', 'dict',
            'set', 'tuple', 'range', 'enumerate', 'zip', 'map',
            'filter', 'sum', 'min', 'max', 'sorted', 'reversed'
        }
        
        # Find all identifiers
        identifiers = set(re.findall(identifier_pattern, code))
        
        # Filter out keywords and builtins
        identifiers = {
            id for id in identifiers 
            if id not in keywords and id not in builtins
        }
        
        # Skip if no identifiers to rename
        if not identifiers:
            return code
            
        # Generate random replacements
        replacements = {}
        used_names = set()
        
        for identifier in identifiers:
            # Generate random name length between 4 and 15
            length = self._rng.randint(4, 15)
            # Include some numbers for variety
            if self._rng.random() > 0.7:
                replacement = self._generate_random_name(length)
            else:
                replacement = self._generate_random_name(length)
            replacements[identifier] = replacement
            used_names.add(replacement)
        
        # Apply replacements
        for old, new in replacements.items():
            # Use word boundaries to avoid partial matches
            code = re.sub(rf'\b{old}\b', new, code)
            
        return code
    
    def _generate_random_name(self, length: int) -> str:
        """Generate a random identifier name"""
        # First character must be letter or underscore
        first_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'
        other_chars = first_chars + '0123456789'
        
        name = self._rng.choice(first_chars)
        for _ in range(length - 1):
            name += self._rng.choice(other_chars)
            
        return name
    
    def _add_unique_markers(self, code: str) -> str:
        """Add unique markers that change every run"""
        marker = f"# JOCKY_{self.hash_gen.generate_script_hash('marker')['custom']}\n"
        return marker + code
    
    def _get_transform_log(self) -> List[str]:
        """Get log of transformations applied"""
        return [
            "Randomized identifiers",
            "Injected junk code",
            "Flattened control flow",
            "Encrypted string constants",
            "Generated unique hashes",
            "Added unique markers"
        ]
    
    def obfuscate_binary(self, binary_path: str) -> Dict[str, Any]:
        """
        Obfuscate a compiled binary (PE/ELF)
        """
        # Read binary
        with open(binary_path, 'rb') as f:
            binary_data = f.read()
            
        # 1. Modify import table
        modified_imports = self.import_obfuscator.obfuscate_imports(binary_data)
        
        # 2. Add junk sections
        modified_binary = self.junk_injector.inject_junk_section(modified_imports)
        
        # 3. Generate new hashes
        hashes = self.hash_gen.generate_file_hash(modified_binary)
        
        # 4. Generate new entry point (if we can modify it)
        # This would require more sophisticated PE parsing
        
        # Save obfuscated binary
        obfuscated_path = self._save_obfuscated_binary(modified_binary)
        
        return {
            'obfuscated_path': obfuscated_path,
            'hashes': hashes,
            'original_size': len(binary_data),
            'new_size': len(modified_binary)
        }
    
    def _save_obfuscated_binary(self, data: bytes) -> str:
        """Save obfuscated binary to temp file"""
        fd, path = tempfile.mkstemp(suffix='.exe')
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        return path