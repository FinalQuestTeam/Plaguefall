"""Register image_gen poses, quantize to existing PAL2 and pack actor tiles."""
from pathlib import Path
from PIL import Image
import argparse, hashlib, json

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]
PALETTE = json.loads((GAME/'art/cangaco-protagonista-iso60-v2/palette.json').read_text())

def pack(frame):
    data = bytearray()
    for x,y,w,h in [(0,0,32,32),(0,32,32,16)]:
        for tx in range(x,x+w,8):
            for ty in range(y,y+h,8):
                for py in range(8):
                    for px in range(0,8,2):
                        data.append(frame.getpixel((tx+px,ty+py))*16+frame.getpixel((tx+px+1,ty+py)))
    return data

def unpack(data):
    """Decode the actual runtime frame, without regenerating its pixels."""
    frame=Image.new('P',(32,48));frame.putpalette(sum(PALETTE,[])+[0]*720)
    offset=0
    for x,y,w,h in [(0,0,32,32),(0,32,32,16)]:
        for tx in range(x,x+w,8):
            for ty in range(y,y+h,8):
                for py in range(8):
                    for px in range(0,8,2):
                        value=data[offset];offset+=1
                        frame.putpixel((tx+px,ty+py),value>>4)
                        frame.putpixel((tx+px+1,ty+py),value&15)
    assert pack(frame)==data
    return frame

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    source=ROOT/'source/deaths-corrected.png';image=Image.open(source).convert('RGBA')
    raw=bytearray();sheets=[];report=[]
    for row,name in enumerate(['damiao','dinorah']):
        crops=[]
        for col in range(4):
            cell=image.crop((round(col*image.width/4),round(row*image.height/2),round((col+1)*image.width/4),round((row+1)*image.height/2)))
            mask=cell.getchannel('A').point(lambda a:255 if a>=220 else 0)
            assert mask.getbbox(),(name,col)
            cell.putalpha(mask);crops.append(cell.crop(mask.getbbox()))
        # One scale per character keeps body proportions stable through collapse.
        scale=min(32/max(c.width for c in crops),42/max(c.height for c in crops))
        sheet=Image.new('P',(128,48));sheet.putpalette(sum(PALETTE,[])+[0]*720)
        frames=[]
        runtime_name='heroi' if name=='damiao' else 'dinorah'
        runtime=(GAME/f'res/{runtime_name}/frames.bin').read_bytes()
        # The first pose is the exact southeast sprite already used in game.
        original=runtime[18*768:19*768]
        for col,crop in enumerate(crops):
            small=crop.resize((max(1,round(crop.width*scale)),max(1,round(crop.height*scale))),Image.Resampling.NEAREST)
            cell=Image.new('RGBA',(32,48));cell.paste(small,((32-small.width)//2,47-small.height))
            frame=Image.new('P',cell.size);frame.putpalette(sheet.getpalette())
            frame.putdata([0 if a<220 else min(range(1,16),key=lambda i:sum((p-PALETTE[i][k])**2 for k,p in enumerate((r,g,b)))) for r,g,b,a in cell.getdata()])
            if col==0:frame=unpack(original)
            sheet.paste(frame,(col*32,0));raw.extend(pack(frame));frames.append(frame.tobytes())
        assert len(set(frames))==4,(name,'duplicate death poses')
        sheets.append((name,sheet));report.append({'actor':name,'frames':4,'cell':[32,48],'scale':scale,'first_pose':'Exact runtime SE idle frame','first_pose_sha256':hashlib.sha256(original).hexdigest(),'runtime_sha256':hashlib.sha256(runtime).hexdigest()})
    assert len(raw)==6144
    binary=GAME/'res/actors/deaths.bin'
    metadata=json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'rom_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'palette':'Existing PAL2','actors':report},indent=2)+'\n'
    if args.check:
        assert binary.read_bytes()==raw
        assert (ROOT/'export.json').read_text()==metadata
    else:
        binary.parent.mkdir(parents=True,exist_ok=True);binary.write_bytes(raw)
        (ROOT/'export.json').write_text(metadata)
    for name,sheet in sheets:
        path=ROOT/(name+'.png')
        if args.check:assert Image.open(path).tobytes()==sheet.tobytes()
        else:
            sheet.save(path,bits=4,transparency=0)
            sheet.resize((512,192),Image.Resampling.NEAREST).save(ROOT/(name+'-4x.png'),transparency=0)
    print('Actor deaths verified: 8 frames, PAL2, 6144 ROM bytes')

if __name__=='__main__':main()
