import subprocess, io, sys, os

ROOT = r'c:\Users\adity\Desktop\CL-JOBS\CirrusLabs_Internal_Hiring_Portal'
FE = os.path.join(ROOT, 'frontend')

def run(cmd, cwd, out):
    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    text = (p.stdout or '') + (p.stderr or '') + f'\nEXITCODE={p.returncode}\n'
    io.open(out, 'w', encoding='utf-8').write(text)
    print(text[-4000:])

run(r'node_modules\.bin\tsc.cmd --noEmit', FE, os.path.join(ROOT, '_tsc.txt'))
