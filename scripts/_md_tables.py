import re
def load(path):
    T=open(path,encoding='utf-8').read().split('\n')
    tabs=[];h='';i=0
    while i<len(T):
        l=T[i]
        if l.startswith('#'): h=l.strip('# ').strip()
        if l.strip().startswith('|') and (i==0 or not T[i-1].strip().startswith('|')):
            j=i
            while j<len(T) and T[j].strip().startswith('|'): j+=1
            rows=[]
            for ln in T[i:j]:
                cells=[c.strip() for c in ln.strip().strip('|').split('|')]
                if all(re.fullmatch(r':?-+:?',c) for c in cells if c): continue
                rows.append([re.sub(r'\*\*(.+?)\*\*',r'\1',c).replace('`','') for c in cells])
            tabs.append((h,rows)); i=j; continue
        i+=1
    return tabs
