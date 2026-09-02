"""
LLVM Code Generator - UNIVERSAL EDITION
Can run ANY command via system() / run().
"""

from llvmlite import ir
from syntax.nodes import *
import os
import subprocess
import platform
import shutil

class LLVMCodeGenerator:
    def __init__(self):
        if platform.system() == "Windows":
            self.target_triple = "x86_64-pc-windows-gnu"
        else:
            self.target_triple = "x86_64-unknown-linux-gnu"
        
        self.module = ir.Module(name="jocky_module")
        self.module.triple = self.target_triple
        
        self.builder = None
        self.entry_builder = None
        self.function = None
        self.symbols = {}
        self.struct_vars = {}
        self.string_counter = 0
        self.loop_counter = 0
        self.if_counter = 0
        self.agent_name = "hello_world"
        
        self.builtins = {
            'collect_registry': self._emit_collect_registry,
            'get_processes': self._emit_get_processes,
            'get_system_info': self._emit_get_system_info,
            'scan_network': self._emit_scan_network,
            'get_open_windows': self._emit_get_open_windows,
            'pack': self._emit_pack,
            'print': self._emit_print,
            'get_time': self._emit_get_time,      
            'get_random': self._emit_get_random,  
            'md5_hash': self._emit_md5_hash,      
            'get_pid': self._emit_get_pid,
            'system': self._emit_system,   # <--- RUN ANY COMMAND
            'run': self._emit_system,      # <--- RUN ANY COMMAND
        }

    def _emit_system(self, args):
        system = self._get_function("system")
        if not system:
            system_type = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))])
            system = ir.Function(self.module, system_type, name="system")
        cmd_ptr = self._generate_expression(args[0])
        return self.builder.call(system, [cmd_ptr])

    def generate(self, ast: Program, output_file: str = None) -> str:
        self._declare_external_functions()
        self._generate_ir(ast)
        ir_code = str(self.module)
        if output_file:
            self._compile_to_native(ir_code, output_file)
        return ir_code
    
    def _declare_external_functions(self):
        func_types = {
            'jocky_collect_registry': ([ir.PointerType(ir.IntType(8))], ir.PointerType(ir.IntType(8))),
            'jocky_get_processes': ([], ir.PointerType(ir.IntType(8))),
            'jocky_get_system_info': ([], ir.PointerType(ir.IntType(8))),
            'jocky_scan_network': ([], ir.PointerType(ir.IntType(8))),
            'jocky_get_open_windows': ([], ir.PointerType(ir.IntType(8))),
            'jocky_get_time': ([], ir.PointerType(ir.IntType(8))),
            'jocky_get_random': ([], ir.PointerType(ir.IntType(8))),
            'jocky_get_pid': ([], ir.PointerType(ir.IntType(8))),
            'jocky_md5_hash': ([ir.PointerType(ir.IntType(8))], ir.PointerType(ir.IntType(8))),
            'system': ([ir.PointerType(ir.IntType(8))], ir.IntType(32)),
            'printf': ([ir.PointerType(ir.IntType(8))], ir.IntType(32)),
            'jocky_int_to_str': ([ir.IntType(64)], ir.PointerType(ir.IntType(8))),
        }
        for name, (args, ret) in func_types.items():
            func_type = ir.FunctionType(ret, args, var_arg=(name == 'printf'))
            ir.Function(self.module, func_type, name=name)
    
    def _get_function(self, name):
        for f in self.module.functions:
            if f.name == name:
                return f
        return None
    
    def _generate_ir(self, ast: Program):
        for node in ast.body:
            if isinstance(node, AgentDeclaration):
                self.agent_name = node.name
                self._generate_agent(node)
            elif isinstance(node, FunctionDeclaration):
                self._generate_function(node)
            elif isinstance(node, StructDeclaration):
                self._generate_struct(node)
            else:
                raise RuntimeError(f"Unknown AST node: {type(node)}")
    
    def _generate_agent(self, node: AgentDeclaration):
        func_type = ir.FunctionType(ir.PointerType(ir.IntType(8)), [])
        self.function = ir.Function(self.module, func_type, name=node.name)
        entry_block = self.function.append_basic_block(name="entry")
        self.entry_builder = ir.IRBuilder(entry_block)
        main_block = self.function.append_basic_block(name="main")
        self.builder = ir.IRBuilder(main_block)
        self.symbols = {}
        self.struct_vars = {}
        return_value = None
        
        for stmt in node.body:
            if isinstance(stmt, LetStatement):
                self._generate_let(stmt)
            elif isinstance(stmt, ReturnStatement):
                return_value = self._generate_expression(stmt.value)
            elif isinstance(stmt, IfStatement):
                self._generate_if(stmt)
            elif isinstance(stmt, WhileStatement):
                self._generate_while(stmt)
            elif isinstance(stmt, ForStatement):
                self._generate_for(stmt)
            elif isinstance(stmt, PrintStatement):
                self._emit_print(stmt.args)
            elif isinstance(stmt, CallExpression):  # <--- ADDED
                self._generate_call(stmt)            # <--- ADDED
        
        self.entry_builder.branch(main_block)
        
        if return_value is not None:
            if isinstance(return_value.type, ir.IntType):
                func = self._get_function("jocky_int_to_str")
                if not func:
                    func_type = ir.FunctionType(ir.PointerType(ir.IntType(8)), [ir.IntType(64)])
                    func = ir.Function(self.module, func_type, name="jocky_int_to_str")
                result = self.builder.call(func, [return_value])
                self.builder.ret(result)
            else:
                self.builder.ret(return_value)
        else:
            self.builder.ret(ir.Constant(ir.PointerType(ir.IntType(8)), None))
    
    def _generate_function(self, node: FunctionDeclaration):
        param_types = [ir.IntType(64) for _ in node.params]
        func_type = ir.FunctionType(ir.PointerType(ir.IntType(8)), param_types)
        func = ir.Function(self.module, func_type, name=node.name)
        
        entry_block = func.append_basic_block(name="entry")
        self.entry_builder = ir.IRBuilder(entry_block)
        main_block = func.append_basic_block(name="main")
        self.builder = ir.IRBuilder(main_block)
        
        old_symbols = self.symbols.copy()
        old_struct = self.struct_vars.copy()
        old_function = self.function
        self.function = func
        self.symbols = {}
        self.struct_vars = {}
        
        for i, param_name in enumerate(node.params):
            param_ptr = self.entry_builder.alloca(ir.IntType(64), name=param_name)
            self.builder.store(func.args[i], param_ptr)
            self.symbols[param_name] = param_ptr
        
        return_value = None
        for stmt in node.body:
            if isinstance(stmt, LetStatement):
                self._generate_let(stmt)
            elif isinstance(stmt, ReturnStatement):
                return_value = self._generate_expression(stmt.value)
            elif isinstance(stmt, PrintStatement):
                self._emit_print(stmt.args)
            elif isinstance(stmt, CallExpression):  # <--- ADDED
                self._generate_call(stmt)            # <--- ADDED
        
        self.entry_builder.branch(main_block)
        
        if return_value is not None:
            if isinstance(return_value.type, ir.IntType):
                func_int = self._get_function("jocky_int_to_str")
                if not func_int:
                    func_type = ir.FunctionType(ir.PointerType(ir.IntType(8)), [ir.IntType(64)])
                    func_int = ir.Function(self.module, func_type, name="jocky_int_to_str")
                result = self.builder.call(func_int, [return_value])
                self.builder.ret(result)
            else:
                self.builder.ret(return_value)
        else:
            self.builder.ret(ir.Constant(ir.PointerType(ir.IntType(8)), None))
        
        self.symbols = old_symbols
        self.struct_vars = old_struct
        self.function = old_function
    
    def _generate_struct(self, node):
        pass
    
    def _generate_if(self, node):
        self.if_counter += 1
        cond = self._generate_expression(node.cond)
        if isinstance(cond.type, ir.IntType) and cond.type.width == 1:
            cmp = cond
        else:
            cmp = self.builder.icmp_signed('!=', cond, ir.Constant(ir.IntType(64), 0))
        then_block = self.function.append_basic_block(name=f"if_then_{self.if_counter}")
        else_block = self.function.append_basic_block(name=f"if_else_{self.if_counter}")
        end_block = self.function.append_basic_block(name=f"if_end_{self.if_counter}")
        self.builder.cbranch(cmp, then_block, else_block)
        
        self.builder.position_at_start(then_block)
        for stmt in node.then_body:
            if isinstance(stmt, LetStatement):
                self._generate_let(stmt)
            elif isinstance(stmt, ReturnStatement):
                value = self._generate_expression(stmt.value)
                self.builder.ret(value)
            elif isinstance(stmt, PrintStatement):
                self._emit_print(stmt.args)
            elif isinstance(stmt, CallExpression):  # <--- ADDED
                self._generate_call(stmt)            # <--- ADDED
        if not self.builder.block.is_terminated:
            self.builder.branch(end_block)
        
        self.builder.position_at_start(else_block)
        if node.else_body:
            for stmt in node.else_body:
                if isinstance(stmt, LetStatement):
                    self._generate_let(stmt)
                elif isinstance(stmt, ReturnStatement):
                    value = self._generate_expression(stmt.value)
                    self.builder.ret(value)
                elif isinstance(stmt, PrintStatement):
                    self._emit_print(stmt.args)
                elif isinstance(stmt, CallExpression):  # <--- ADDED
                    self._generate_call(stmt)            # <--- ADDED
        if not self.builder.block.is_terminated:
            self.builder.branch(end_block)
        
        self.builder.position_at_start(end_block)
    
    def _generate_while(self, node):
        self.loop_counter += 1
        loop_header = self.function.append_basic_block(name=f"while_header_{self.loop_counter}")
        loop_body = self.function.append_basic_block(name=f"while_body_{self.loop_counter}")
        loop_end = self.function.append_basic_block(name=f"while_end_{self.loop_counter}")
        self.builder.branch(loop_header)
        
        self.builder.position_at_start(loop_header)
        cond = self._generate_expression(node.cond)
        if isinstance(cond.type, ir.IntType) and cond.type.width == 1:
            cmp = cond
        else:
            cmp = self.builder.icmp_signed('!=', cond, ir.Constant(ir.IntType(64), 0))
        self.builder.cbranch(cmp, loop_body, loop_end)
        
        self.builder.position_at_start(loop_body)
        for stmt in node.body:
            if isinstance(stmt, LetStatement):
                self._generate_let(stmt)
            elif isinstance(stmt, ReturnStatement):
                value = self._generate_expression(stmt.value)
                self.builder.ret(value)
            elif isinstance(stmt, PrintStatement):
                self._emit_print(stmt.args)
            elif isinstance(stmt, CallExpression):  # <--- ADDED
                self._generate_call(stmt)            # <--- ADDED
        if not self.builder.block.is_terminated:
            self.builder.branch(loop_header)
        
        self.builder.position_at_start(loop_end)
    
    def _generate_for(self, node):
        start = self._generate_expression(node.start)
        end = self._generate_expression(node.end)
        counter_ptr = self.entry_builder.alloca(ir.IntType(64), name="for_counter")
        self.builder.store(start, counter_ptr)
        self.loop_counter += 1
        loop_header = self.function.append_basic_block(name=f"for_header_{self.loop_counter}")
        loop_body = self.function.append_basic_block(name=f"for_body_{self.loop_counter}")
        loop_end = self.function.append_basic_block(name=f"for_end_{self.loop_counter}")
        self.builder.branch(loop_header)
        
        self.builder.position_at_start(loop_header)
        counter = self.builder.load(counter_ptr)
        cmp = self.builder.icmp_signed('<', counter, end)
        self.builder.cbranch(cmp, loop_body, loop_end)
        
        self.builder.position_at_start(loop_body)
        self.symbols[node.var] = counter_ptr
        for stmt in node.body:
            if isinstance(stmt, LetStatement):
                self._generate_let(stmt)
            elif isinstance(stmt, ReturnStatement):
                value = self._generate_expression(stmt.value)
                self.builder.ret(value)
            elif isinstance(stmt, PrintStatement):
                self._emit_print(stmt.args)
            elif isinstance(stmt, CallExpression):  # <--- ADDED
                self._generate_call(stmt)            # <--- ADDED
        if not self.builder.block.is_terminated:
            new_val = self.builder.add(counter, ir.Constant(ir.IntType(64), 1))
            self.builder.store(new_val, counter_ptr)
            self.builder.branch(loop_header)
        
        self.builder.position_at_start(loop_end)
    
    def _generate_let(self, node):
        value = self._generate_expression(node.value)
        if isinstance(node.value, StructLiteral):
            self.struct_vars[node.name] = node.value
        if node.name in self.symbols:
            ptr = self.symbols[node.name]
            self.builder.store(value, ptr)
        else:
            ptr = self.entry_builder.alloca(value.type, name=node.name)
            self.builder.store(value, ptr)
            self.symbols[node.name] = ptr
    
    def _generate_expression(self, node):
        if isinstance(node, StringLiteral):
            return self._generate_string(node.value)
        elif isinstance(node, NumberLiteral):
            return ir.Constant(ir.IntType(64), int(node.value))
        elif isinstance(node, Identifier):
            return self._generate_identifier(node.name)
        elif isinstance(node, CallExpression):
            return self._generate_call(node)
        elif isinstance(node, BinaryOperation):
            return self._generate_binary(node)
        elif isinstance(node, ArrayLiteral):
            return self._generate_array(node)
        elif isinstance(node, ArrayIndex):
            return self._generate_array_index(node)
        elif isinstance(node, StructLiteral):
            return ir.Constant(ir.PointerType(ir.IntType(8)), None)
        elif isinstance(node, StructFieldAccess):
            obj_name = node.struct.name
            if obj_name in self.struct_vars:
                struct_node = self.struct_vars[obj_name]
                for field in struct_node.fields:
                    if field.name == node.field_name:
                        return self._generate_expression(field.value)
            raise RuntimeError(f"Struct field '{node.field_name}' not found for '{obj_name}'")
        elif isinstance(node, StructField):
            return self._generate_expression(node.value)
        else:
            raise RuntimeError(f"Unknown expression: {type(node)}")
    
    def _generate_string(self, value):
        self.string_counter += 1
        name = f".str_{self.string_counter}"
        encoded_value = value.encode('utf-8')
        str_type = ir.ArrayType(ir.IntType(8), len(encoded_value) + 1)
        str_const = ir.Constant(str_type, bytearray(encoded_value) + b'\x00')
        global_var = ir.GlobalVariable(self.module, str_type, name=name)
        global_var.initializer = str_const
        global_var.global_constant = True
        global_var.linkage = 'internal'
        return self.builder.bitcast(global_var, ir.PointerType(ir.IntType(8)))
    
    def _generate_identifier(self, name):
        if name in self.symbols:
            return self.builder.load(self.symbols[name])
        raise RuntimeError(f"Undefined variable: {name}")
    
    def _generate_call(self, node):
        if node.name in self.builtins:
            return self.builtins[node.name](node.args)
        
        func = self._get_function(node.name)
        if func:
            args = [self._generate_expression(arg) for arg in node.args]
            return self.builder.call(func, args)
        return self._emit_external_call(node)
    
    def _generate_binary(self, node):
        left = self._generate_expression(node.left)
        right = self._generate_expression(node.right)
        ops = {
            '+': self.builder.add,
            '-': self.builder.sub,
            '*': self.builder.mul,
            '/': self.builder.sdiv,
            '==': lambda l, r: self.builder.icmp_signed('==', l, r),
            '!=': lambda l, r: self.builder.icmp_signed('!=', l, r),
            '<': lambda l, r: self.builder.icmp_signed('<', l, r),
            '>': lambda l, r: self.builder.icmp_signed('>', l, r),
            '<=': lambda l, r: self.builder.icmp_signed('<=', l, r),
            '>=': lambda l, r: self.builder.icmp_signed('>=', l, r),
        }
        if node.op in ops:
            return ops[node.op](left, right)
        raise RuntimeError(f"Unknown operator: {node.op}")
    
    def _generate_array(self, node):
        if node.elements:
            return self._generate_expression(node.elements[0])
        return ir.Constant(ir.PointerType(ir.IntType(8)), None)
    
    def _generate_array_index(self, node):
        arr = self._generate_expression(node.array)
        idx = self._generate_expression(node.index)
        return arr
    
    def _generate_struct_literal(self, node):
        return ir.Constant(ir.PointerType(ir.IntType(8)), None)
    
    def _generate_struct_field(self, node):
        return self._generate_expression(node.value)
    
    def _emit_collect_registry(self, args):
        func = self._get_function("jocky_collect_registry")
        if not func:
            func_type = ir.FunctionType(ir.PointerType(ir.IntType(8)), [ir.PointerType(ir.IntType(8))])
            func = ir.Function(self.module, func_type, name="jocky_collect_registry")
        arg = self._generate_expression(args[0])
        return self.builder.call(func, [arg])
    
    def _emit_get_processes(self, args):
        func = self._get_function("jocky_get_processes")
        if not func:
            func_type = ir.FunctionType(ir.PointerType(ir.IntType(8)), [])
            func = ir.Function(self.module, func_type, name="jocky_get_processes")
        return self.builder.call(func, [])
    
    def _emit_get_system_info(self, args):
        func = self._get_function("jocky_get_system_info")
        if not func:
            func_type = ir.FunctionType(ir.PointerType(ir.IntType(8)), [])
            func = ir.Function(self.module, func_type, name="jocky_get_system_info")
        return self.builder.call(func, [])
    
    def _emit_scan_network(self, args):
        func = self._get_function("jocky_scan_network")
        if not func:
            func_type = ir.FunctionType(ir.PointerType(ir.IntType(8)), [])
            func = ir.Function(self.module, func_type, name="jocky_scan_network")
        return self.builder.call(func, [])

    def _emit_get_open_windows(self, args):
        func = self._get_function("jocky_get_open_windows")
        if not func:
            func_type = ir.FunctionType(ir.PointerType(ir.IntType(8)), [])
            func = ir.Function(self.module, func_type, name="jocky_get_open_windows")
        return self.builder.call(func, [])
    
    def _emit_get_time(self, args):
        func = self._get_function("jocky_get_time")
        if not func:
            func_type = ir.FunctionType(ir.PointerType(ir.IntType(8)), [])
            func = ir.Function(self.module, func_type, name="jocky_get_time")
        return self.builder.call(func, [])

    def _emit_get_random(self, args):
        func = self._get_function("jocky_get_random")
        if not func:
            func_type = ir.FunctionType(ir.PointerType(ir.IntType(8)), [])
            func = ir.Function(self.module, func_type, name="jocky_get_random")
        return self.builder.call(func, [])

    def _emit_md5_hash(self, args):
        func = self._get_function("jocky_md5_hash")
        if not func:
            func_type = ir.FunctionType(ir.PointerType(ir.IntType(8)), [ir.PointerType(ir.IntType(8))])
            func = ir.Function(self.module, func_type, name="jocky_md5_hash")
        arg = self._generate_expression(args[0])
        return self.builder.call(func, [arg])

    def _emit_get_pid(self, args):
        func = self._get_function("jocky_get_pid")
        if not func:
            func_type = ir.FunctionType(ir.PointerType(ir.IntType(8)), [])
            func = ir.Function(self.module, func_type, name="jocky_get_pid")
        return self.builder.call(func, [])
    
    def _emit_pack(self, args):
        if args:
            return self._generate_expression(args[0])
        return ir.Constant(ir.PointerType(ir.IntType(8)), None)
    
    def _emit_print(self, args):
        printf = self._get_function("printf")
        if not printf:
            printf_type = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))], var_arg=True)
            printf = ir.Function(self.module, printf_type, name="printf")
        if args:
            arg_value = self._generate_expression(args[0])
            is_string = isinstance(arg_value.type, ir.PointerType) and isinstance(arg_value.type.pointee, ir.IntType) and arg_value.type.pointee.width == 8
            
            if is_string:
                fmt = self._generate_string("%s\n")
            else:
                fmt = self._generate_string("%d\n")
            return self.builder.call(printf, [fmt, arg_value])
        return ir.Constant(ir.IntType(32), 0)
    
    def _emit_external_call(self, node):
        func_type = ir.FunctionType(ir.VoidType(), [])
        func = ir.Function(self.module, func_type, name=node.name)
        return self.builder.call(func, [])
    
    def _compile_to_native(self, ir_code, output_file):
        print(f"   🔧 Compiling to {output_file}...")
        ll_file = f"{output_file}.ll"
        with open(ll_file, 'w') as f:
            f.write(ir_code)
        
        agent_name = self.agent_name if self.agent_name else "hello_world"
        c_file = f"{output_file}_runtime.c"
        self._create_c_runtime(c_file, agent_name)
        
        obj_file = f"{output_file}.o"
        print(f"   ⏳ Converting LLVM IR to object file...")
        llc_path = shutil.which("llc")
        if not llc_path:
            msys_paths = ["C:/msys64/mingw64/bin/llc", "C:/msys64/usr/bin/llc"]
            for p in msys_paths:
                if os.path.exists(p) or os.path.exists(p + ".exe"):
                    llc_path = p
                    break
        if llc_path:
            try:
                subprocess.run([llc_path, "-mtriple", "x86_64-pc-windows-gnu", "-filetype=obj", ll_file, "-o", obj_file],
                             check=True, capture_output=True, text=True)
                print(f"   ✅ Object file generated: {obj_file}")
            except subprocess.CalledProcessError as e:
                print(f"   ⚠️  llc error: {e.stderr}")
                obj_file = None
        else:
            obj_file = None
        
        c_obj = f"{output_file}_runtime.o"
        compiler = 'gcc'
        try:
            subprocess.run([compiler, "-c", c_file, "-o", c_obj], check=True, capture_output=True, text=True)
            print(f"   ✅ C runtime compiled: {c_obj}")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ C compilation failed: {e.stderr}")
            return
        
        try:
            cmd = [compiler, "-o", f"{output_file}.exe"]
            if obj_file and os.path.exists(obj_file):
                cmd.append(obj_file)
            cmd.append(c_obj)
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"   ✅ Compiled: {output_file}.exe")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Linking failed: {e.stderr}")
            try:
                subprocess.run([compiler, "-o", f"{output_file}.exe", c_obj], check=True, capture_output=True, text=True)
                print(f"   ✅ Compiled (C only): {output_file}.exe")
            except subprocess.CalledProcessError as e2:
                print(f"   ❌ Still failed: {e2.stderr}")
    
    def _create_c_runtime(self, c_file, agent_name):
        c_code = get_jocky_c_runtime(agent_name)
        with open(c_file, 'w') as f:
            f.write(c_code)

def compile_to_llvm(ast: Program, output_file: str = None) -> str:
    generator = LLVMCodeGenerator()
    return generator.generate(ast, output_file)

def generate_llvm_ir(ast: Program) -> str:
    generator = LLVMCodeGenerator()
    return generator.generate(ast, output_file=None)

# ==========================================
# UNIVERSAL C RUNTIME (System calls allowed)
# ==========================================
def get_jocky_c_runtime(agent_name: str) -> str:
    return f"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <windows.h>
#include <locale.h>
#include <fcntl.h>
#include <io.h>

extern char* {agent_name}();

char* jocky_int_to_str(long long val) {{ char* result = malloc(64); snprintf(result, 64, "%lld", val); return result; }}
char* jocky_get_time() {{ char* result = malloc(64); static int c = 0; c++; sprintf(result, "%lld", (long long)GetTickCount() + c); return result; }}
char* jocky_get_random() {{ char* result = malloc(64); static int c = 0; c++; sprintf(result, "%d", (rand() + c) % 1000000); return result; }}
char* jocky_get_pid() {{ char* result = malloc(64); sprintf(result, "%d", GetCurrentProcessId()); return result; }}
char* jocky_md5_hash(const char* input) {{ unsigned long h = 5381; int c; while ((c = *input++)) h = ((h << 5) + h) + c; char* result = malloc(64); sprintf(result, "%lx", h); return result; }}

char* jocky_get_system_info() {{ char* result = malloc(200); sprintf(result, "{{\\"os\\":\\"Windows\\",\\"version\\":\\"10.0\\",\\"arch\\":\\"x64\\",\\"cores\\":8}}"); return result; }}
char* jocky_get_processes() {{ char* result = malloc(200); sprintf(result, "[{{\\"pid\\":1234,\\"name\\":\\"svchost.exe\\"}},{{\\"pid\\":5678,\\"name\\":\\"explorer.exe\\"}}]"); return result; }}
char* jocky_collect_registry(const char* hive) {{ char* result = malloc(300); sprintf(result, "{{\\"OneDrive\\":\\"C:\\\\Users\\\\user\\\\OneDrive\\",\\"Teams\\":\\"C:\\\\Users\\\\user\\\\AppData\\\\Local\\\\Microsoft\\\\Teams\\"}}"); return result; }}
char* jocky_scan_network() {{ char* result = malloc(300); sprintf(result, "{{\\"output\\":\\"Windows IP Configuration\\\\n   IPv4 Address: 192.168.1.100\\\\n   Subnet Mask: 255.255.255.0\\"}}"); return result; }}
char* jocky_get_open_windows() {{ char* result = malloc(500); sprintf(result, "[{{\\"title\\":\\"JOCKY - Hackathon\\",\\"class\\":\\"Chrome_WidgetWin_1\\",\\"hwnd\\":123456}},{{\\"title\\":\\"Visual Studio Code\\",\\"class\\":\\"Chrome_WidgetWin_1\\",\\"hwnd\\":789012}}]"); return result; }}

int main() {{
    srand((unsigned int)time(NULL));
    SetConsoleOutputCP(65001);
    printf("=== JOCKY Starting ===\\n");
    char* result = {agent_name}();
    if (result) {{ printf("%s\\n", result); }}
    printf("=== JOCKY Finished ===\\n");
    return 0;
}}
"""