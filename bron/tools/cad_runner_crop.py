"""Hulpfuncties voor tools/cad_runner_views.py: pdf renderen (toleranties weg via cad_clean), uitsnijden, navy maken."""
import sys, subprocess, tempfile, os, numpy as np
from PIL import Image
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from cad_clean import erase_mask
Image.MAX_IMAGE_PIXELS=None
NAVY=(29,26,77)
def render(pdf,W=5000):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(['pdftoppm','-gray','-scale-to-x',str(W),'-scale-to-y','-1','-png','-singlefile',pdf,d+'/p'],check=True,stderr=subprocess.DEVNULL)
        g=np.array(Image.open(d+'/p.png').convert('L')).astype(np.float32)
    em,_=erase_mask(pdf,g.shape)
    if em is not None: g[em]=255
    return g
def crop(g,fr,blanks=()):
    H,W=g.shape; x0,y0,x1,y1=[int(v*s) for v,s in zip(fr,(W,H,W,H))]
    c=g[y0:y1,x0:x1].copy()
    for a,b,cc,e in blanks:   # fractions of page
        X0,Y0,X1,Y1=int(a*W)-x0,int(b*H)-y0,int(cc*W)-x0,int(e*H)-y0
        c[max(0,Y0):max(0,Y1),max(0,X0):max(0,X1)]=255
    ys,xs=np.where(c<200)
    return c[ys.min():ys.max()+1,xs.min():xs.max()+1]
def rgba(c):
    al=np.clip((255-c)*1.3,0,255).astype(np.uint8)
    r=np.zeros(c.shape+(4,),np.uint8); r[...,0],r[...,1],r[...,2]=NAVY; r[...,3]=al
    return Image.fromarray(r,'RGBA')
if __name__=='__main__':
    pdf,out=sys.argv[1],sys.argv[2]
    g=render(pdf)
    Image.fromarray(g.astype(np.uint8)).resize((g.shape[1]//4,g.shape[0]//4)).save(out)
