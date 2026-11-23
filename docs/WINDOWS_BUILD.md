# Build the Windows desktop distribution

Complete QUICKSTART.md first. Use Windows Python 3.11 and allow several GB of free build space. Assemble the vision artifacts before packaging. For genuine advisory, download the pinned PTE/tokenizer and build the x86-64 native worker in WSL; put worker and libllama_runner.so under `llama/bin/x86_64`.

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.venv\Scripts\python.exe tools\build_windows.py
dist_hardening\BlisterTrace\BlisterTrace.exe --desktop
```

The executable keeps its legacy filename for compatibility; visible branding is Medge Vision. Distribute the complete `dist_hardening/BlisterTrace` directory, including `_internal`, models and sidecars. Copying only the EXE will not work. Configuration is normalized to the distribution paths. `validation/windows_build.json` reports actual model/worker presence; a completed PyInstaller build is not proof that Llama generation or Hailo inference ran.

Windows vision uses ONNX CPU. Windows advisory uses WSL; this is not a Windows Hailo driver or native Windows Llama implementation. The final repository packaging corrections have been syntax-checked, but a new complete EXE was not built during this backup task because storage is limited. Historical station/Windows build evidence must not be described as a fresh-clone build test.
