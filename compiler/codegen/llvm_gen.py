from llvmlite import ir
from llvmlite import binding as llvm
from syntax.nodes import *

class LLVMCodeGenerator:
    def __init__(self):
        self.module = None
        self.builder = None
        self.function = None
        self.context = None
        
    def generate(self, ast: Program) -> str:
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        
        self.module = ir.Module(name="jocky_module")
        
        for node in ast.body:
            if isinstance(node, AgentDeclaration):
                self._generate_agent(node)
        
        return str(self.module)
    
    def _generate_agent(self, node: AgentDeclaration):
        func_type = ir.FunctionType(ir.VoidType(), [])
        self.function = ir.Function(self.module, func_type, name=node.name)
        
        block = self.function.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        
        for stmt in node.body:
            if isinstance(stmt, LetStatement):
                self._generate_let(stmt)
            elif isinstance(stmt, ReturnStatement):
                self._generate_return(stmt)
        
        self.builder.ret_void()
    
    def _generate_let(self, node: LetStatement):
        pass
    
    def _generate_return(self, node: ReturnStatement):
        pass

def compile_to_llvm(ast: Program) -> str:
    generator = LLVMCodeGenerator()
    return generator.generate(ast)
