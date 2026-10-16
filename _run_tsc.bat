@echo off
cd /d c:\Users\adity\Desktop\CL-JOBS\CirrusLabs_Internal_Hiring_Portal\frontend
call node_modules\.bin\tsc.cmd --noEmit > c:\Users\adity\Desktop\CL-JOBS\CirrusLabs_Internal_Hiring_Portal\_tsc.txt 2>&1
echo EXITCODE=%errorlevel% >> c:\Users\adity\Desktop\CL-JOBS\CirrusLabs_Internal_Hiring_Portal\_tsc.txt
