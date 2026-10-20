"""Explore ordinary weighted place-transition nets with explicit incomplete bounds."""
import argparse, json, pathlib, sys

def need(ok, message):
    if not ok: raise ValueError(message)

def integer(n, low=0, high=10**9):
    need(type(n) is int and low <= n <= high, 'integer outside supported range')
    return n

def ident(s):
    need(type(s) is str and 0 < len(s) <= 80, 'invalid identifier')
    return s

def fields(obj, required, optional=()):
    need(type(obj) is dict and set(required) <= set(obj) <= set(required)|set(optional), 'missing or unknown fields')

def unique_pairs(pairs):
    out={}
    for k,v in pairs:
        need(k not in out, 'duplicate JSON key')
        out[k]=v
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=pathlib.Path);a=p.parse_args()
    try:
        with a.input.open('rb') as f: raw=f.read(1048577)
        need(len(raw) <= 1048576, 'input exceeds 1 MiB')
        doc=json.loads(raw.decode('utf-8'),object_pairs_hook=unique_pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
        out=analyze(doc);print(json.dumps(out,ensure_ascii=True,sort_keys=True));return out.get('exit_code',0)
    except (ValueError,OSError,UnicodeError,RecursionError,OverflowError) as e:
        print(str(e),file=sys.stderr);return 2


from collections import deque

def analyze(doc):
    fields(doc,('initial','transitions','token_limit','state_limit'),('terminal',))
    need(type(doc['initial']) is dict and 1<=len(doc['initial'])<=32,'expected 1..32 places');places=sorted(ident(p) for p in doc['initial']);start=tuple(integer(doc['initial'][p]) for p in places)
    cap=integer(doc['token_limit'],1,1000000);limit=integer(doc['state_limit'],1,10000);need(max(start)<=cap,'initial marking exceeds exploration bound')
    need(type(doc['transitions']) is list and len(doc['transitions'])<=100,'too many transitions');trans={}
    for t in doc['transitions']:
        fields(t,('id','consume','produce'));k=ident(t['id']);need(k not in trans,'duplicate transition')
        arcs=[]
        for side in ('consume','produce'):
            need(type(t[side]) is dict and set(t[side])<=set(places),'unknown place in arc')
            arcs.append(tuple(integer(t[side].get(p,0)) for p in places))
        trans[k]=arcs
    need(type(doc.get('terminal',[])) is list and len(doc.get('terminal',[]))<=100,'too many terminal markings');terminal=set()
    for m in doc.get('terminal',[]):
        need(type(m) is dict and set(m)==set(places),'terminal marking must name every place');terminal.add(tuple(integer(m[p]) for p in places))
    queue=deque([start]);parent={start:None};via={};deadlocks=[];deadlock_count=0;cutoffs=0;fired=set();explored=0
    def trace(mark):
        steps=[]
        while parent[mark] is not None:steps.append(via[mark]);mark=parent[mark]
        return list(reversed(steps))
    while queue:
        mark=queue.popleft();explored+=1;enabled=[]
        for k,(consume,produce) in sorted(trans.items()):
            if all(n>=c for n,c in zip(mark,consume)):
                enabled.append(k);fired.add(k);nxt=tuple(n-c+p for n,c,p in zip(mark,consume,produce))
                if max(nxt)>cap:cutoffs+=1;continue
                if nxt not in parent:
                    if len(parent)>=limit:cutoffs+=1;continue
                    parent[nxt]=mark;via[nxt]=k;queue.append(nxt)
        if not enabled and mark not in terminal:
            deadlock_count+=1
            if not deadlocks:deadlocks.append({'marking':dict(zip(places,mark)),'transitions':trace(mark)})
    complete=cutoffs==0
    return {'complete':complete,'explored_states':explored,'cutoff_edges':cutoffs,'deadlock_count':deadlock_count,'shortest_deadlock':deadlocks[0] if deadlocks else None,'never_enabled_in_explored_states':sorted(set(trans)-fired),'status':'deadlock_found' if deadlocks else 'no_deadlock' if complete else 'unknown','exit_code':1 if deadlocks else 0 if complete else 3}

if __name__ == '__main__':
    raise SystemExit(main())
