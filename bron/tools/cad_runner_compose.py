"""Klikrunner-pallets: tekening van de 9-pootjespallet + de onderlat eronder (zelfde schaal) -> input/cad/<artikel-id>.png.
De lijst staat onderaan; runner.json zegt tools/datasheets.py welk onderschrift erbij hoort.
Gebruik: python3 tools/cad_runner_compose.py
"""
import numpy as np, json, os
from PIL import Image
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAD=os.path.join(ROOT,'input/cad')+'/'
def longest_run(a, ymax_frac=1.0, ymin_frac=0.0):
    """(length, x0, y) of the longest horizontal run of ink in the top part of the image"""
    best=(0,0,0)
    H=a.shape[0]
    for y in range(int(H*ymin_frac), int(H*ymax_frac)):
        row=a[y]>90
        if row.sum()<best[0]: continue
        d=np.diff(np.concatenate([[0],row.astype(np.int8),[0]]))
        st=np.where(d==1)[0]; en=np.where(d==-1)[0]
        if len(st)==0: continue
        k=np.argmax(en-st); L=en[k]-st[k]
        if L>best[0]: best=(L,st[k],y)
    return best
RUN={'low':1170,'1111':1100,'1140':1140,'1212':1200,'cp5':1163}
CENTER={'cp5'}   # onderlat langer dan de pallet: midden onder de pallet zetten
# CP5-tekening: boven- en onderrand lopen door in de hulplijnen van de maat 764; daarom de maatlijn 1140 meten (56-64% van de hoogte)
PBAND={'cp5':(0.56,0.64)}
def compose(base_id, runner, pallet_len, out_id):
    P=Image.open(CAD+base_id+'.png').convert('RGBA'); pa=np.array(P)[...,3]
    lo,hi=PBAND.get(runner,(0.0,0.75))
    pl,px0,py=longest_run(pa,hi,lo)
    R=Image.open(CAD+f'runner-views/runner_{runner}.png').convert('RGBA'); ra=np.array(R)[...,3]
    rl,rx0,ry=longest_run(ra,1.0)
    s=(pl/pallet_len)/(rl/RUN[runner])
    R2=R.resize((max(1,round(R.width*s)),max(1,round(R.height*s))),Image.LANCZOS)
    gap=int(P.height*0.06)
    W=max(P.width, px0 + R2.width + 10); H=P.height+gap+R2.height+10
    C=Image.new('RGBA',(W,H),(29,26,77,0)); C.alpha_composite(P,(0,0)); rx=px0+round(pl/2)-round((rx0+rl/2)*s) if runner in CENTER else px0-round(rx0*s)
    if rx<0:
        C2=Image.new('RGBA',(W-rx,H),(29,26,77,0)); C2.alpha_composite(C,(-rx,0)); C=C2; rx=0
    elif rx+R2.width>C.width:
        C2=Image.new('RGBA',(rx+R2.width+10,H),(29,26,77,0)); C2.alpha_composite(C,(0,0)); C=C2
    C.alpha_composite(R2,(rx,P.height+gap))
    C.save(CAD+out_id+'.png',optimize=True)
    return (pl,rl,round(s,3),C.size)
if __name__=='__main__':
    J=[('qp1111lb9fr','1111',1100,'qp1111lb3rr'),('qp1140lb9fr','1140',1140,'qp1140lb3rr'),('qp1212lb9fr','1212',1200,'qp1212lb3rr'),
       ('qp1208lb9fr','low',1200,'qp1208lb3rr'),('qp1208lb9fr-art','low',1200,'qp1208lb3rr-art'),('2-qp1208lb9fr','low',1200,'2-qp1208lb3rr'),
       ('1-qp1208lb9fr-cd','low',1200,'qp1208lb3rr-cd'),('qp1208lb9fr-cd','low',1200,'3-qp1208lb3rr-cd'),('2-qp1208lb9fr-cd','low',1200,'2-qp1208lb3rr-cd'),
       ('qp1210lb9fr','low',1200,'qp1210lb3rr'),('n-qp1210lb9fr-cd','low',1200,'qp1210lb3rr-cd'),('qp1210lb9fr-cd','low',1200,'2-qp1210lb3rr-cd'),
       ('qp76114lb9fr','cp5',1140,'qp76114lb3rr'),('qp76114lb9fr-cd','cp5',1140,'qp76114lb3rr-cd')]
    for b,r,L,o in J:
        print(o, compose(b,r,L,o))
    json.dump([o for *_,o in J], open(CAD+'runner.json','w'), indent=1)
