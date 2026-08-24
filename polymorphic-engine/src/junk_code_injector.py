import random
import string

class JunkCodeInjector:
    """Inject useless code to increase binary size and confuse analysis"""
    
    def __init__(self):
        self.junk_templates = self._generate_templates()
    
    def _generate_templates(self) -> list:
        """Generate random junk code templates"""
        templates = []
        
        # Template 1: Unused variable assignments
        def var_template():
            var_name = ''.join(random.choices(string.ascii_letters, k=8))
            return f"{var_name} = {random.randint(1, 1000)}"
        templates.append(var_template)
        
        # Template 2: Useless calculations
        def calc_template():
            x = random.randint(1, 10)
            y = random.randint(1, 10)
            return f"_ = {x} * {y} + {random.randint(1, 5)}"
        templates.append(calc_template)
        
        # Template 3: Empty loops
        def loop_template():
            return f"for _ in range({random.randint(1, 5)}): pass"
        templates.append(loop_template)
        
        # Template 4: String operations
        def string_template():
            chars = ''.join(random.choices(string.ascii_letters, k=5))
            return f'"{chars}".upper() if {random.randint(0, 1)} else "{chars}".lower()'
        templates.append(string_template)
        
        return templates
    
    def inject(self, code: str) -> str:
        """Inject junk code at random positions"""
        lines = code.split('\n')
        
        # Random number of junk lines to inject (5-15% of original lines)
        num_junk = int(len(lines) * random.uniform(0.05, 0.15))
        
        # Inject at random positions
        for _ in range(num_junk):
            pos = random.randint(0, len(lines) - 1)
            template = random.choice(self.junk_templates)
            junk_line = template()
            
            # Add indentation to match surrounding code
            if pos < len(lines):
                indent = self._get_indentation(lines[pos])
                lines.insert(pos, indent + junk_line)
            else:
                lines.append(junk_line)
        
        return '\n'.join(lines)
    
    def _get_indentation(self, line: str) -> str:
        """Get indentation of a line"""
        return line[:len(line) - len(line.lstrip())]