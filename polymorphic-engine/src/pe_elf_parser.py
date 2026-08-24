import pefile
import struct
import random

class PEElfParser:
    """Parse PE/ELF files for binary-level obfuscation"""
    
    def parse_pe(self, file_path: str) -> dict:
        """Parse PE file and extract sections"""
        try:
            pe = pefile.PE(file_path)
            
            sections = []
            for section in pe.sections:
                sections.append({
                    'name': section.Name.decode('utf-8', 'ignore'),
                    'virtual_address': section.VirtualAddress,
                    'virtual_size': section.Misc_VirtualSize,
                    'raw_size': section.SizeOfRawData,
                    'raw_data': section.get_data()
                })
            
            return {
                'entry_point': pe.OPTIONAL_HEADER.AddressOfEntryPoint,
                'image_base': pe.OPTIONAL_HEADER.ImageBase,
                'sections': sections,
                'imports': self._get_imports(pe)
            }
        except:
            return {'error': 'Failed to parse PE'}
    
    def _get_imports(self, pe) -> list:
        """Extract imported functions"""
        imports = []
        if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                dll_name = entry.dll.decode('utf-8', 'ignore')
                for imp in entry.imports:
                    if imp.name:
                        imports.append({
                            'dll': dll_name,
                            'function': imp.name.decode('utf-8', 'ignore')
                        })
        return imports