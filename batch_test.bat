@echo off
REM === Batch QA complet DeadBot crowd ===

set PLUGIN_EXE=dist\deadbot.exe

REM CPU DIAG + shutdown
echo Testing: cpu_diag
echo {"tool_calls":[{"func":"cpu_diag"},{"func":"shutdown"}],"messages":[{"role":"system","content":"Diagnose CPU."},{"role":"user","content":"cpu_diag"}]} | %PLUGIN_EXE%
echo.

REM GPU DIAG + shutdown
echo Testing: gpu_diag
echo {"tool_calls":[{"func":"gpu_diag"},{"func":"shutdown"}],"messages":[{"role":"system","content":"Diagnose GPU."},{"role":"user","content":"gpu_diag"}]} | %PLUGIN_EXE%
echo.

REM PERF DIAG + shutdown
echo Testing: perf_diag
echo {"tool_calls":[{"func":"perf_diag"},{"func":"shutdown"}],"messages":[{"role":"system","content":"Diagnose Perf."},{"role":"user","content":"perf_diag"}]} | %PLUGIN_EXE%
echo.
