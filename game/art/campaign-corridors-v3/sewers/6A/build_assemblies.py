from pathlib import Path
from PIL import Image
import numpy as np,json
HERE=Path(__file__).resolve().parent;OUT=HERE/'cycle2-candidate';OUT.mkdir(exist_ok=True)
PALETTE=[(0,0,0),(1,1,1),(1,2,3),(1,3,4),(2,4,5),(3,4,4),(3,3,2),(4,4,3),(5,5,4),(6,6,5),(3,2,1),(4,3,1),(5,4,2),(7,6,3),(1,2,1),(2,2,2)];RGB=[tuple(v*255//7 for v in c)for c in PALETTE];USE=[1,2,4,6,8,10,12,13]
BOXES={'cistern':([16,12,760,490],[240,160]),'bridge':([520,176,1120,676],[192,160]),'maintenance':([910,26,1680,686],[240,208]),'refuge':([1664,24,2160,680],[160,216])}
def convert(src,box,size,grid=4):
 crop=src.crop(box);scale=min(size[0]/crop.width,size[1]/crop.height);nw,nh=int(crop.width*scale)//grid*grid,int(crop.height*scale)//grid*grid;im=crop.resize((max(1,nw//grid),max(1,nh//grid)),Image.Resampling.NEAREST).resize((nw,nh),Image.Resampling.NEAREST);a=np.asarray(im,dtype=np.int32);pal=np.array([RGB[i]for i in USE],dtype=np.int32);ix=((a[:,:,None]-pal[None,None])**2).sum(3).argmin(2);rgb=np.array(RGB,dtype=np.uint8)[np.array(USE)[ix]];rgba=np.concatenate([rgb,np.full((nh,nw,1),255,dtype=np.uint8)],2);rgba[a.max(2)<28,3]=0;o=Image.new('RGBA',size);o.alpha_composite(Image.fromarray(rgba),(((size[0]-nw)//2)//grid*grid,((size[1]-nh)//2)//grid*grid));return o,scale
if __name__=='__main__':
 src=Image.open(HERE/'source/whole-v2-clean.png').convert('RGB');r={}
 for name,(box,size)in BOXES.items():
  im,scale=convert(src,box,size);im.save(OUT/f'{name}.png');r[name]={'source_rect':box,'size':size,'uniformScale':scale,'pixelGridBeforePacking':4,'colorSubset':USE}
 (OUT/'modules.json').write_text(json.dumps(r,indent=2)+'\n')
