"""Small CUDA Driver/NVRTC binding. NVIDIA performs compilation and execution.
Only Windows x64 is supported. Every CUDA result is checked; no CPU fallback.
"""
import ctypes as C
import os
from pathlib import Path
import sys
import numpy as np

class CUDAError(RuntimeError): pass

class DeviceBuffer:
    def __init__(self, driver, size):
        self.driver, self.size = driver, int(size)
        self.ptr = C.c_uint64()
        driver.check(driver.dll.cuMemAlloc_v2(C.byref(self.ptr), self.size), 'allocate GPU memory')
    def upload(self, array):
        array = np.ascontiguousarray(array)
        if array.nbytes > self.size: raise ValueError('GPU upload exceeds allocation')
        self.driver.check(self.driver.dll.cuMemcpyHtoD_v2(self.ptr, array.ctypes.data, array.nbytes), 'upload')
        return self
    def download(self, dtype, shape):
        out = np.empty(shape, dtype=dtype)
        if out.nbytes > self.size: raise ValueError('GPU download exceeds allocation')
        self.driver.check(self.driver.dll.cuMemcpyDtoH_v2(out.ctypes.data, self.ptr, out.nbytes), 'download')
        return out
    def close(self):
        if self.ptr.value:
            self.driver.check(self.driver.dll.cuMemFree_v2(self.ptr), 'free GPU memory')
            self.ptr.value = 0
    def __enter__(self): return self
    def __exit__(self,*args): self.close()

class Driver:
    def __init__(self, source, device=0):
        if os.name != 'nt': raise CUDAError('This CUDA engine requires Windows x64 and an NVIDIA driver.')
        try: self.dll = C.WinDLL('nvcuda.dll')
        except OSError as e: raise CUDAError('NVIDIA CUDA driver not found. Install the official NVIDIA driver.') from e
        signatures = {
            'cuInit':[C.c_uint], 'cuDeviceGetCount':[C.POINTER(C.c_int)], 'cuDeviceGet':[C.POINTER(C.c_int),C.c_int],
            'cuDeviceGetName':[C.c_void_p,C.c_int,C.c_int],
            'cuDeviceGetAttribute':[C.POINTER(C.c_int),C.c_int,C.c_int],
            'cuDevicePrimaryCtxRetain':[C.POINTER(C.c_void_p),C.c_int],
            'cuCtxSetCurrent':[C.c_void_p], 'cuMemGetInfo_v2':[C.POINTER(C.c_size_t),C.POINTER(C.c_size_t)],
            'cuMemAlloc_v2':[C.POINTER(C.c_uint64),C.c_size_t], 'cuMemFree_v2':[C.c_uint64],
            'cuMemcpyHtoD_v2':[C.c_uint64,C.c_void_p,C.c_size_t], 'cuMemcpyDtoH_v2':[C.c_void_p,C.c_uint64,C.c_size_t],
            'cuModuleLoadData':[C.POINTER(C.c_void_p),C.c_void_p],
            'cuModuleGetFunction':[C.POINTER(C.c_void_p),C.c_void_p,C.c_char_p],
            'cuLaunchKernel':[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.POINTER(C.c_void_p),C.c_void_p],
            'cuCtxSynchronize':[], 'cuGetErrorName':[C.c_int,C.POINTER(C.c_char_p)],
            'cuEventCreate':[C.POINTER(C.c_void_p),C.c_uint],'cuEventRecord':[C.c_void_p,C.c_void_p],
            'cuEventSynchronize':[C.c_void_p], 'cuEventElapsedTime':[C.POINTER(C.c_float),C.c_void_p,C.c_void_p], 'cuEventDestroy_v2':[C.c_void_p],
        }
        for name,args in signatures.items():
            f=getattr(self.dll,name);f.argtypes=args;f.restype=C.c_int
        self.check(self.dll.cuInit(0),'initialize CUDA')
        count=C.c_int();self.check(self.dll.cuDeviceGetCount(C.byref(count)),'discover GPUs');self.device_count=count.value
        self.devices=[]
        for index in range(count.value):
            dv=C.c_int();self.check(self.dll.cuDeviceGet(C.byref(dv),index),'discover device');nm=C.create_string_buffer(256);self.check(self.dll.cuDeviceGetName(nm,256,dv.value),'read device name');self.devices.append(dict(index=index,name=nm.value.decode()))
        dev=C.c_int();self.check(self.dll.cuDeviceGet(C.byref(dev),int(device)),'select GPU');self.device=dev.value
        name=C.create_string_buffer(256);self.check(self.dll.cuDeviceGetName(name,256,self.device),'GPU name');self.name=name.value.decode()
        major,minor=C.c_int(),C.c_int()
        self.check(self.dll.cuDeviceGetAttribute(C.byref(major),75,self.device),'compute capability')
        self.check(self.dll.cuDeviceGetAttribute(C.byref(minor),76,self.device),'compute capability')
        self.arch=f'compute_{major.value}{minor.value}'
        self.context=C.c_void_p();self.check(self.dll.cuDevicePrimaryCtxRetain(C.byref(self.context),self.device),'retain CUDA context')
        self.activate()
        self.module=C.c_void_p();ptx=self.compile(source)
        self.check(self.dll.cuModuleLoadData(C.byref(self.module),C.cast(C.create_string_buffer(ptx),C.c_void_p)),'load CUDA kernels')
        self.functions={};self.gpu_ms=0
    def check(self,result,action):
        if result:
            message=C.c_char_p();self.dll.cuGetErrorName(result,C.byref(message))
            raise CUDAError(f'CUDA failed to {action}: {(message.value or str(result).encode()).decode()}')
    def activate(self): self.check(self.dll.cuCtxSetCurrent(self.context),'activate CUDA context')
    def memory(self):
        free,total=C.c_size_t(),C.c_size_t();self.check(self.dll.cuMemGetInfo_v2(C.byref(free),C.byref(total)),'read VRAM');return free.value,total.value
    def buffer(self,array):
        a=np.ascontiguousarray(array);return DeviceBuffer(self,a.nbytes).upload(a)
    def allocate(self,size): return DeviceBuffer(self,size)
    def launch(self,name,count,*args):
        if name not in self.functions:
            fn=C.c_void_p();self.check(self.dll.cuModuleGetFunction(C.byref(fn),self.module,name.encode()),'find kernel '+name);self.functions[name]=fn
        values=[C.c_uint64(a.ptr.value) if isinstance(a,DeviceBuffer) else C.c_uint(a) if isinstance(a,np.uint32) else C.c_int(a) for a in args]
        params=(C.c_void_p*len(values))(*(C.cast(C.byref(a),C.c_void_p) for a in values))
        start,end=self.event(),self.event()
        try:
            self.check(self.dll.cuEventRecord(start,None),'record kernel start')
            self.check(self.dll.cuLaunchKernel(self.functions[name],(count+255)//256,1,1,256,1,1,0,None,params,None),'launch '+name)
            self.check(self.dll.cuEventRecord(end,None),'record kernel end');self.check(self.dll.cuEventSynchronize(end),'finish kernel')
            elapsed=C.c_float();self.check(self.dll.cuEventElapsedTime(C.byref(elapsed),start,end),'measure kernel');self.gpu_ms+=elapsed.value
        finally:
            self.dll.cuEventDestroy_v2(start);self.dll.cuEventDestroy_v2(end)
    def sync(self): self.check(self.dll.cuCtxSynchronize(),'synchronize kernels')
    def event(self):
        e=C.c_void_p();self.check(self.dll.cuEventCreate(C.byref(e),0),'create timing event');return e
    def compile(self,source):
        candidates=[]
        for base in [Path(__file__).parent/'.runtime'/'deps',*map(Path,sys.path)]:
            folder=base/'nvidia'/'cuda_nvrtc'/'bin'
            if folder.is_dir(): candidates.extend(folder.glob('nvrtc64*.dll'))
        cuda=os.environ.get('CUDA_PATH')
        if cuda: candidates.extend((Path(cuda)/'bin').glob('nvrtc64*.dll'))
        candidates=[p for p in candidates if 'builtins' not in p.name and '.alt' not in p.name]
        if not candidates: raise CUDAError('NVRTC is missing. Run launch.ps1 to install NVIDIA runtime compiler dependencies.')
        selected=candidates[0];self.dll_directory=os.add_dll_directory(str(selected.parent))
        self.builtins=[C.WinDLL(str(p)) for p in selected.parent.glob('nvrtc-builtins64*.dll')]
        os.environ['PATH']=str(selected.parent)+os.pathsep+os.environ.get('PATH','')
        nv=C.CDLL(str(selected))
        nv.nvrtcCreateProgram.argtypes=[C.POINTER(C.c_void_p),C.c_char_p,C.c_char_p,C.c_int,C.c_void_p,C.c_void_p]
        nv.nvrtcCompileProgram.argtypes=[C.c_void_p,C.c_int,C.POINTER(C.c_char_p)]
        nv.nvrtcGetProgramLogSize.argtypes=[C.c_void_p,C.POINTER(C.c_size_t)];nv.nvrtcGetProgramLog.argtypes=[C.c_void_p,C.c_void_p]
        nv.nvrtcGetPTXSize.argtypes=[C.c_void_p,C.POINTER(C.c_size_t)];nv.nvrtcGetPTX.argtypes=[C.c_void_p,C.c_void_p]
        nv.nvrtcDestroyProgram.argtypes=[C.POINTER(C.c_void_p)]
        program=C.c_void_p();result=nv.nvrtcCreateProgram(C.byref(program),source.encode(),b'nulltype.cu',0,None,None)
        if result: raise CUDAError(f'NVRTC program creation failed: {result}')
        try:
            options=[b'--std=c++14',f'--gpu-architecture={self.arch}'.encode()]
            result=nv.nvrtcCompileProgram(program,len(options),(C.c_char_p*len(options))(*options))
            if result:
                size=C.c_size_t();nv.nvrtcGetProgramLogSize(program,C.byref(size));log=C.create_string_buffer(size.value);nv.nvrtcGetProgramLog(program,log)
                raise CUDAError('CUDA kernel compilation failed:\n'+log.value.decode())
            size=C.c_size_t();nv.nvrtcGetPTXSize(program,C.byref(size));ptx=C.create_string_buffer(size.value);nv.nvrtcGetPTX(program,ptx)
            return ptx.raw
        finally: nv.nvrtcDestroyProgram(C.byref(program))
