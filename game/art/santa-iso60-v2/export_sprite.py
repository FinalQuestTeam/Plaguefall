"""Technical registration/indexing of image_gen artwork; no procedural statue art."""
from pathlib import Path
import argparse, hashlib, json, struct
from PIL import Image
ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[1]

def generate():
    source=ROOT/'originals/santa.png'
    rgba=Image.open(source).convert('RGBA')
    rgba.putalpha(rgba.getchannel('A').point(lambda a:255 if a>=128 else 0))
    box=rgba.getbbox();assert box
    crop=rgba.crop(box)
    ratio=min(38/crop.width,46/crop.height)
    crop=crop.resize((round(crop.width*ratio),round(crop.height*ratio)),Image.Resampling.NEAREST)
    frame=Image.new('RGBA',(40,48))
    frame.paste(crop,((40-crop.width)//2,47-crop.height))
    words=struct.unpack('>16H',(GAME/'res/stages/05/palette.bin').read_bytes())
    colors=[(((c>>1)&7)*255//7,((c>>5)&7)*255//7,((c>>9)&7)*255//7) for c in words]
    native=Image.new('P',frame.size);native.putpalette([v for c in colors for v in c]+[0]*720)
    native.putdata([0 if a<128 else min(range(1,16),key=lambda i:sum((colors[i][j]-rgb[j])**2 for j in range(3))) for *rgb,a in frame.getdata()])
    native.info['transparency']=0
    # The crown lies in the top third. Pick its gold highlight centroid rather
    # than hard-coding a glow position unrelated to the generated drawing.
    gold=[(x,y) for y in range(16) for x in range(40) if native.getpixel((x,y)) in (9,10,11)]
    assert gold
    crown=[176+round(sum(p[0] for p in gold)/len(gold))-4,176+round(sum(p[1] for p in gold)/len(gold))-4]
    report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'native_size':[40,48],
        'native_bounds':list(native.getbbox()),'world_origin':[176,176],'erase_rect':[176,160,40,64],
        'solid_rect':[176,176,40,48],'crown':crown,'palette':'stage05 PAL3, unchanged',
        'camera':'High camera target 60 degrees above ground; visual match, not a measurable 3D calibration.',
        'technical_export':'Alpha threshold, crop, nearest-neighbour registration and existing palette indexing only.',
        'generation':'Built-in image_gen; final camera correction prompt in prompt-camera-final.txt'}
    return native,report

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    native,report=generate()
    if args.check:
        saved=Image.open(ROOT/'santa.png');assert saved.mode=='P' and saved.size==(40,48)
        assert saved.tobytes()==native.tobytes() and saved.info['transparency']==0
        assert json.loads((ROOT/'export.json').read_text())==report
    else:
        native.save(ROOT/'santa.png',bits=4,transparency=0)
        native.convert('RGBA').resize((320,384),Image.Resampling.NEAREST).save(ROOT/'santa-8x.png')
        (ROOT/'export.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
