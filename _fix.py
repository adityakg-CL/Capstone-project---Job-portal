import io
P = 'frontend/src/App.tsx'
L = io.open(P, encoding='utf-8').read().split('\n')
# Lines 425..426 (1-based) are the orphaned demo JSX body + closing brace.
# Find the second 'function JobDetailApi(' and delete the stub just before it.
idx = [i for i, l in enumerate(L) if l.startswith('function JobDetailApi(')]
print('JobDetailApi at', [i + 1 for i in idx])
second = idx[1]
# delete from second-2 .. second-1  (the 'return <>...' line and its '}' line)
print('deleting:', repr(L[second - 2][:70]), '|', repr(L[second - 1][:30]))
del L[second - 2:second]
io.open(P, 'w', encoding='utf-8', newline='').write('\n'.join(L))
print('now', len(L), 'lines')
