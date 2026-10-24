"""Geometry helpers shared by authored maps and actual-controller probes."""
from collections import deque
import math

def free(d,x,y,margin=0,extra=()):
    l,t,r,b=d['bounds']
    return (l+margin<=x<=r-15-margin and t+margin<=y<=b-15-margin
            and not any(x<a+w+margin and x+16>a-margin and y<c+h+margin and y+16>c-margin for a,c,w,h,*_ in [*d['solids'],*extra]))

def closest(d,x,y,extra=(),margin=0):
    l,t,r,b=d['bounds']
    return min(((a,c) for a in range(l,r-14,8) for c in range(t,b-14,8) if free(d,a,c,margin,extra)),key=lambda p:abs(p[0]-x)+abs(p[1]-y))

def path(d,start,goal,margin=8):
    """8px orthogonal centerline with an additional8px navigation margin."""
    start=tuple(start);goal=tuple(goal)
    assert free(d,*start) and free(d,*goal),(start,goal,'invalid endpoint')
    q=deque([start]);seen={start:None}
    while q:
        p=q.popleft()
        if p==goal:break
        for n in ((p[0]+8,p[1]),(p[0]-8,p[1]),(p[0],p[1]+8),(p[0],p[1]-8)):
            if n not in seen and (n==goal or free(d,*n,margin)):
                seen[n]=p;q.append(n)
    assert goal in seen,('no controller route',start,goal,margin)
    result=[];p=goal
    while p is not None:result.append(list(p));p=seen[p]
    result.reverse()
    return [p for i,p in enumerate(result) if i in (0,len(result)-1) or (result[i-1][0]==p[0])!=(result[i+1][0]==p[0])]

def route(d,points):
    result=[list(d['start'])]
    for goal in points:
        if list(goal)==result[-1]:continue
        result.extend(path(d,result[-1],goal)[1:])
    return result

def faces(d,solids=None):
    """Only launch collision probes from free space, on actual visible faces."""
    probes=[]
    for a,c,w,h,*_ in d['solids'] if solids is None else solids:
        candidates=[]
        for y in range(c,c+h,8):
            candidates.extend([(a-24,y,7,'px',a-16,1),(a+w+8,y,6,'px',a+w,-1)])
        for x in range(a,a+w,8):
            candidates.extend([(x,c-24,5,'py',c-16,1),(x,c+h+8,4,'py',c+h,-1)])
        done=set()
        for p in candidates:
            if p[2] not in done and free(d,p[0],p[1]):probes.append(p);done.add(p[2])
    return probes

def edges(d):
    l,t,r,b=d['bounds'];out=[]
    for button,axis,limit,points in [(6,'px',l,((l,y) for y in range(t,b-14,8))),(7,'px',r-15,((r-15,y) for y in range(t,b-14,8))),(4,'py',t,((x,t) for x in range(l,r-14,8))),(5,'py',b-15,((x,b-15) for x in range(l,r-14,8)))]:
        p=next((p for p in points if free(d,*p)),None)
        if p:out.append((*p,button,axis,limit))
    return out

def validate(d):
    start=tuple(d['start']);assert free(d,*start),('blocked start',start)
    q=deque([start]);seen={start}
    while q:
        x,y=q.popleft()
        for p in ((x+8,y),(x-8,y),(x,y+8),(x,y-8)):
            if p not in seen and free(d,*p):seen.add(p);q.append(p)
    l,t,r,b=d['bounds'];allfree={(x,y) for x in range(l,r-14,8) for y in range(t,b-14,8) if free(d,x,y)}
    assert seen==allfree,('disconnected walkable positions',len(seen),len(allfree))
    samples=0
    for a,b in zip(d['points'],d['points'][1:]):
        steps=math.ceil(math.dist(a,b))
        for i in range(steps+1):
            x=round(a[0]+(b[0]-a[0])*i/max(1,steps))-8;y=round(a[1]+(b[1]-a[1])*i/max(1,steps))-8
            assert free(d,x,y),('NPC route collision',a,b,x,y)
            samples+=1
    return dict(footprint=16,free_positions=len(allfree),reachable_positions=len(seen),all_free_positions_connected=True,swept16pxSamples=samples)
