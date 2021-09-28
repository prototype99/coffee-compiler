#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug  4 09:38:36 2021

@author: ryan
"""

__name__ = 'CoffeeUtil'

class Symbol():
    def __init__(self, id:str, name:str, size:int, line:int):
        self.id:str = id
        self.name:str = name
        self.size:int = size
        self.line:int = line

class Var(Symbol):
    LOCAL:int = 0
    GLOBAL:int = 1
    
    def __init__(self, id:str, data_type:str, size:int, scope:int, is_array:bool, line:int):
        super().__init__(id, 'var', size, line)
        self.data_type:str = data_type
        self.scope:int = scope
        self.is_array:bool = is_array
        self.addr:int = 0
        
class Method(Symbol):
    def __init__(self, id:str, return_type:str, line:int):
        super().__init__(id, 'method', 0, line)
        self.return_type:str = return_type
        self.param:list = []
        self.data:str = ''
        self.body:str = ''
        self.has_return:bool = False

    def pushParam(self, param:str):
        self.param.append(param)

class Import(Method):
    def __init__(self, id:str, return_type:str, line:int):
        super().__init__(id, return_type, line)
        self.name = 'import'

class Loop(Symbol):
    def __init__(self, id:str, continue_label:str, end_label:str, line:int):
        super().__init__(id, 'loop', 0, line)
        self.continue_label:str = continue_label
        self.end_label:str = end_label

class StackFrame:
    def __init__(self):
        self.scope:list = []
        self.stack_ptr:int = 0
        self.pushScope()
    
    def pushScope(self):
        self.scope.append([])
    
    def popScope(self):
        self.scope.pop()
    
    def pushBytes(self, bytes):
        self.stack_ptr -= bytes
    
    def popBytes(self, bytes):
        self.stack_ptr += bytes
        
    def pushVar(self, var:Var):
        self.scope[-1].append(var)
        
        if var.scope == Var.LOCAL:
            self.pushBytes(var.size)
            var.addr = self.stack_ptr
    
    def pushMethod(self, method:Method):
        self.scope[-1].append(method)
        
class SymbolTable:
    param_reg = ['%rdi','%rsi','%rdx','%rcx','%r8','%r9']
    
    def __init__(self):
        self.label_count:int = -1
        self.stack_frame:list = []
        self.method_ctx:list = []
        self.loop_ctx:list = []
    
    def pushFrame(self, method_ctx):
        self.stack_frame.append(StackFrame())
        self.pushMethodContext(method_ctx)
    
    def popFrame(self):
        self.popMethodContext()
        self.stack_frame.pop()
    
    def pushScope(self):
        self.stack_frame[-1].pushScope()
    
    def popScope(self):
        self.stack_frame[-1].popScope()
    
    def pushBytes(self, bytes:int):
        self.stack_frame[-1].pushBytes(bytes)
        
    def popBytes(self, bytes:int):
        self.stack_frame[-1].popBytes(bytes)
    
    def pushVar(self, var:Var):
        self.stack_frame[-1].pushVar(var)
    
    def pushMethod(self, method:Method):
        self.stack_frame[-1].pushMethod(method)
        
    def pushMethodContext(self, method:Method):
        self.method_ctx.append(method)
        
    def popMethodContext(self):
        self.method_ctx.pop()
    
    def pushLoopContext(self, loop:Loop):
        self.loop_ctx.append(loop)
        
    def popLoopContext(self):
        self.loop_ctx.pop()
        
    def find(self, id:str):
        for i in range(len(self.stack_frame)-1,-1,-1):
            for j in range(len(self.stack_frame[i].scope)-1,-1,-1):
                for symbol in self.stack_frame[i].scope[j]:
                    if symbol.id == id:
                        return symbol
        return None
        
    def peek(self, id:str):
        for symbol in self.stack_frame[-1].scope[-1]:
            if symbol.id == id:
                return symbol
        return None
    
    def getNextLabel(self):
        self.label_count += 1
        return '.LC' + str(self.label_count)
        
    def getStackPtr(self):
        return self.stack_frame[-1].stack_ptr
    
    def getMethodContext(self):
        return self.method_ctx[-1]
    
    def getLoopContext(self):
        if (len(self.loop_ctx) > 0):
            return self.loop_ctx[-1]
        else:
            return None
