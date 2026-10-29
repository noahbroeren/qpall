"""Onderlat-tekeningen (klikbare onderlatten) uitsnijden: bovenaanzicht + zijaanzicht -> input/cad/runner-views/runner_<type>.png.
Gebruik: python3 tools/cad_runner_views.py <map-met-pdfs>   (Drive-id's staan in de code)
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cad_runner_crop import *
P=(sys.argv[1] if len(sys.argv) > 1 else 'input/cad/pdf') + '/'   # pdf's als <Drive-id>.pdf
OUT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'input/cad/runner-views')
spec={
 'low':(P+'1Zk07VOIEN2W7zCqBlbmj3NC-aQN5ASvW.pdf',(0.08,0.11,0.68,0.365),[(0.215,0.225,0.29,0.26)],(0.08,0.40,0.664,0.515),[(0.185,0.405,0.23,0.445),(0.185,0.47,0.23,0.515)]),
}
spec['1111']=(P+'1gNFHECGDupYO6SQVDlopVvq83s20rDz4.pdf',(0.04,0.122,0.611,0.31),[],(0.04,0.385,0.576,0.425),[])
spec['1140']=(P+'137HJodzanjRXUmMSm2wYnh14D6pPHdCW.pdf',(0.04,0.127,0.625,0.325),[],(0.04,0.375,0.598,0.405),[])
spec['1212']=(P+'1nl4SQxjvTpU59Sd9Sx9-8PSRniDyx-sj.pdf',(0.04,0.135,0.652,0.33),[(0.63,0.215,0.67,0.34)],(0.04,0.445,0.625,0.478),[])
for k,(pdf,tf,tb,sf,sb) in spec.items():
    g=render(pdf)
    t=crop(g,tf,tb); s=crop(g,sf,sb)
    gap=60; W=max(t.shape[1],s.shape[1]); H=t.shape[0]+gap+s.shape[0]
    c=np.full((H,W),255,np.float32); c[:t.shape[0],:t.shape[1]]=t; c[t.shape[0]+gap:,:s.shape[1]]=s
    rgba(c).save(os.path.join(OUT, f'runner_{k}.png')); print(k,c.shape)
