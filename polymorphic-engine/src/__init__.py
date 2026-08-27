"""
JOCKY Polymorphic Engine
Member C's Component - Makes every deployment unique
"""

from .obfuscator import PolymorphicObfuscator
from .variable_encryption import VariableEncryptor
from .control_flow_flattener import ControlFlowFlattener
from .import_table_obfuscator import ImportTableObfuscator
from .junk_code_injector import JunkCodeInjector
from .hash_generator import HashGenerator

__all__ = [
    'PolymorphicObfuscator',
    'VariableEncryptor',
    'ControlFlowFlattener',
    'ImportTableObfuscator',
    'JunkCodeInjector',
    'HashGenerator'
]