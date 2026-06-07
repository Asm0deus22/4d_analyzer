import os
os.add_dll_directory("C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v13.0\\bin\\x64")
import pycuda.driver as cuda
import pycuda.autoinit
from pycuda.compiler import SourceModule
import numpy as np

class CUDASolver:
    def __init__(self):
        # компиляция CUDA ядра
        with open("kernelCUDA", "r") as file:
            self.mod = SourceModule(file.read())
        # подготовка словаря со всеми данными
        self.memory = {}
    def getFunction(self, title):
        return self.mod.get_function(title)
    def allocMemory(self, nbytes, name):
        if name in self.memory:
            raise KeyError("Cannot alloc non unique sector")
        self.memory[name] = cuda.mem_alloc(nbytes)
        return self.memory[name]
    def copyToMemory(self, npArr, name):
        if not (name in self.memory):
            raise KeyError("Not found memory sector")
        cuda.memcpy_htod(self.memory[name], npArr)
    def copyFromMemory(self, npArr, name):
        if not (name in self.memory):
            raise KeyError("Not found memory sector")
        cuda.memcpy_dtoh(npArr, self.memory[name])
    def freeMemory(self, name):
        if not (name in self.memory):
            raise KeyError("Not found memory sector")
        self.memory[name].free()
        del self.memory[name]
    def freeAllMemory(self):
        for name in list(self.memory.keys()):
            self.freeMemory(name)
    def __del__(self):
        self.freeAllMemory()
