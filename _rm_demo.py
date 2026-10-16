import io
P = 'frontend/src/App.tsx'
L = io.open(P, encoding='utf-8').read().split('\n')
start = next(i for i, l in enumerate(L) if l.startswith('function JobDetail('))
end = next(i for i, l in enumerate(L) if l.startswith('function JobDetailApi('))
print('removing lines', start + 1, 'to', end, repr(L[start][:60]), '...', repr(L[end - 1][:40]))
del L[start:end]
io.open(P, 'w', encoding='utf-8', newline='').write('\n'.join(L))
print('now', len(L), 'lines')
