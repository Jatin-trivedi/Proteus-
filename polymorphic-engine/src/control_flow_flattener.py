"""
Control Flow Flattener - Makes control flow analysis difficult
"""

import ast
import random
import hashlib
from typing import Dict, Any, List, Optional

class ControlFlowFlattener:
    """
    Flattens control flow by converting branches to switch statements
    and adding opaque predicates
    """
    
    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._seed = seed
        self._state_var = f"_cf_state_{self._rng.randint(1000, 9999)}"
        
    def flatten_control_flow(self, code: str) -> str:
        """
        Flatten control flow in the given code
        Adds opaque predicates and dispatcher logic
        """
        try:
            # Parse AST
            tree = ast.parse(code)
            
            # Find functions with control flow
            transformer = ControlFlowTransformer(self._state_var, seed=self._seed)
            transformed = transformer.visit(tree)
            
            # Convert back to code
            import astor
            ast.fix_missing_locations(transformed)
            flattened_code = astor.to_source(transformed)
            
            # Add dispatcher preamble
            preamble = self._generate_dispatcher_preamble()
            
            return preamble + flattened_code
            
        except Exception as e:
            # If transformation fails, return original code
            # with some basic obfuscation
            return self._simple_obfuscation(code)
    
    def _generate_dispatcher_preamble(self) -> str:
        """Generate the dispatcher code"""
        return f'''
# JOCKY Control Flow Dispatcher
{self._state_var} = 0

def _jocky_dispatch(state):
    global {self._state_var}
    {self._state_var} = state
    return state
'''
    
    def _simple_obfuscation(self, code: str) -> str:
        """Simple fallback obfuscation if AST transformation fails"""
        # Add opaque predicates
        lines = code.split('\n')
        obfuscated = []
        
        for line in lines:
            # Add random dead code
            if 'if' in line and ':' in line and not line.strip().startswith('#'):
                if self._rng.random() > 0.5:
                    dead_code = f"if {self._rng.randint(0, 999)} == {self._rng.randint(0, 999)}: pass"
                    obfuscated.append(f"# {dead_code}")
            obfuscated.append(line)
            
        return '\n'.join(obfuscated)

class ControlFlowTransformer(ast.NodeTransformer):
    """AST transformer for control flow flattening"""
    
    def __init__(self, state_var: str, seed: Optional[int] = None):
        self.state_var = state_var
        self._rng = random.Random(seed)
        self._block_counter = 0
        self._blocks = {}
        
    def visit_FunctionDef(self, node):
        """Transform function bodies"""
        # Store original body
        original_body = node.body
        
        # Create dispatcher
        dispatcher = self._create_dispatcher(original_body)
        
        # Replace body with dispatcher
        node.body = dispatcher
        
        return node
    
    def _create_dispatcher(self, body: List[ast.stmt]) -> List[ast.stmt]:
        """Create a dispatcher for the function body"""
        # Split body into basic blocks
        blocks = self._split_into_blocks(body)
        
        # Use deterministic state IDs so the initial state reaches the first block.
        block_ids = {index: block for index, block in enumerate(blocks)}
        self._blocks.update(block_ids)
            
        # Create dispatcher while loop
        dispatch_var = ast.Name(id=self.state_var, ctx=ast.Store())
        
        # Create switch-like dispatch
        if_stmt = self._create_dispatch_if(block_ids)
        
        # Wrap in while loop
        while_loop = ast.While(
            test=ast.Constant(value=True),
            body=[if_stmt],
            orelse=[]
        )
        
        # Initialize state
        init_state = ast.Assign(
            targets=[dispatch_var],
            value=ast.Constant(value=0)
        )
        
        return [init_state, while_loop]
    
    def _split_into_blocks(self, body: List[ast.stmt]) -> List[List[ast.stmt]]:
        """Split AST body into basic blocks"""
        blocks = []
        current_block = []
        
        for stmt in body:
            current_block.append(stmt)
            
            # If this is a control flow statement, end the block
            if isinstance(stmt, (ast.If, ast.For, ast.While, ast.Return)):
                if current_block:
                    blocks.append(current_block)
                    current_block = []
                    
        if current_block:
            blocks.append(current_block)
            
        return blocks
    
    def _create_dispatch_if(self, block_ids: Dict[int, List[ast.stmt]]) -> ast.If:
        """Create if-elif chain for dispatch"""
        test = ast.Compare(
            left=ast.Name(id=self.state_var, ctx=ast.Load()),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=0)]
        )
        
        block_items = list(block_ids.items())

        def build_chain(index: int) -> ast.If:
            block_id, block = block_items[index]
            block_body = list(block)

            if index + 1 < len(block_items):
                block_body.append(ast.Assign(
                    targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
                    value=ast.Constant(value=block_items[index + 1][0])
                ))
                orelse = [build_chain(index + 1)]
            else:
                # A function without an explicit return still exits normally.
                block_body.append(ast.Break())
                orelse = []

            dispatch_test = ast.Compare(
                left=ast.Name(id=self.state_var, ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=block_id)]
            )
            return ast.If(test=dispatch_test, body=block_body, orelse=orelse)

        return build_chain(0)