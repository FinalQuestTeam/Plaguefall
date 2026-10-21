"""Pack approved image_gen option B for the VDP, reserving core-only glow inks."""
from pathlib import Path
import argparse, hashlib, json, struct
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]
SOURCE = ROOT.parent / 'concepts/titulo-v1/b-ex-voto.png'

def export():
    rgb = np.asarray(Image.open(SOURCE).convert('RGB').resize((320,224), Image.Resampling.LANCZOS)).astype(np.int32)
    yy, xx = np.indices((224,320))
    mask = (xx >= 151) & (xx <= 170) & (yy >= 64) & (yy <= 125) & (rgb[:,:,0] > 75) & (rgb[:,:,0] > rgb[:,:,1]*1.6) & (rgb[:,:,0] > rgb[:,:,2]*2)
    tiles = rgb.reshape(28,8,40,8,3).transpose(0,2,1,3,4).reshape(1120,64,3)
    masks = mask.reshape(28,8,40,8).transpose(0,2,1,3).reshape(1120,64)
    groups = (tiles.mean(axis=(1,2)) > 45).astype(int)
    glow = np.array([[146,0,0],[219,36,0],[255,109,0]])
    for iteration in range(8):
        pals=[]
        for group in range(2):
            pixels=tiles[groups==group][~masks[groups==group]]
            quant=Image.fromarray(pixels.astype('uint8').reshape(1,-1,3)).quantize(colors=12,method=Image.Quantize.MEDIANCUT)
            values=np.asarray(quant.getpalette()[:36]).reshape(12,3)
            colors=[(0,0,0)]
            for v in np.rint(values*7/255).astype(int)*255//7:
                c=tuple(v)
                if c not in colors: colors.append(c)
            candidates,counts=np.unique(np.rint(pixels*7/255).astype(int)*255//7,axis=0,return_counts=True)
            while len(colors)<13:
                errors=((candidates[:,None]-np.asarray(colors)[None])**2).sum(axis=2).min(axis=1)
                n=int((errors*counts).argmax())
                if errors[n]==0: break
                colors.append(tuple(candidates[n]))
            colors += [(0,0,0)]*(13-len(colors))
            pals.append(np.concatenate([np.asarray(colors),glow]))
        distances=[]
        for pal in pals:
            d=((tiles[:,:,None]-pal[None,None])**2).sum(axis=3)
            d[:,:,13:]=np.where(masks[:,:,None],d[:,:,13:],10000000)
            d[:,:,:13]=np.where(masks[:,:,None],10000000,d[:,:,:13])
            distances.append(d)
        chosen=np.stack([d.min(axis=2).sum(axis=1) for d in distances],axis=1).argmin(axis=1)
        if np.array_equal(chosen,groups): break
        groups=chosen
    indices=np.stack([d.argmin(axis=2) for d in distances])[chosen,np.arange(1120)]
    native=np.stack(pals)[chosen[:,None],indices].reshape(28,40,8,8,3).transpose(0,2,1,3,4).reshape(224,320,3).astype('uint8')
    packed=bytes((indices[:,::2]*16+indices[:,1::2]).astype('uint8').flat)
    words=[sum(round(int(c)*7/255)<<(1+4*i) for i,c in enumerate(v)) for pal in pals for v in pal]
    assets={'tiles.bin':packed,'groups.bin':bytes(chosen.astype('uint8')),'palettes.bin':struct.pack('>32H',*words)}
    assert np.array_equal(indices>=13,masks)
    return assets,Image.fromarray(native),Image.fromarray((mask*255).astype('uint8')),dict(source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),size=[320,224],tiles=1120,glowing_pixels=int(mask.sum()),glow_indices=[13,14,15],glow_region=[151,64,170,125],generation='Approved built-in image_gen option B; deterministic resize and hardware palette conversion',prompt='../concepts/titulo-v1/prompts/b-ex-voto.txt')

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true'); args=parser.parse_args()
    assets,image,mask,report=export()
    for name,data in assets.items():
        dest=GAME/'res/titlecard'/name
        if args.check: assert dest.read_bytes()==data,name
        else: dest.write_bytes(data)
    if args.check:
        assert Image.open(ROOT/'title-native.png').tobytes()==image.tobytes()
    else:
        image.save(ROOT/'title-native.png'); image.resize((960,672),Image.Resampling.NEAREST).save(ROOT/'title-3x.png'); mask.save(ROOT/'core-mask.png')
        (ROOT/'export.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
