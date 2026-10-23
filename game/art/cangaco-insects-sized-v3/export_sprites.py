"""Export image_gen redraws at the project-defined native sizes; no procedural poses."""
from pathlib import Path
from PIL import Image
import importlib.util,json,re,hashlib,argparse
ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[1]
spec=importlib.util.spec_from_file_location('source_pipeline',GAME/'art/cangaco-insects-iso60-v2/export_sprites.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)

def pieces(size):
    if size<=32:return [(0,0,size,size)]
    return [(0,0,32,32),(0,32,32,16),(32,0,16,32),(32,32,16,16)]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--partial',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
    catalog=json.loads((GAME/'art/cangaco-insects-iso60-v2/catalog.json').read_text())
    corrections=json.loads((ROOT/'direction_corrections.json').read_text())
    raw=bytearray();icons=bytearray(15*512);report=[];definitions=[]
    for e in catalog:
        id=e['id'];file=ROOT/'originals'/(id+'.png')
        size=int(re.search(r'\.size\s*=\s*(\d+)',(GAME/'src/enemies/defs'/(id+'.c')).read_text()).group(1))
        assert size in (16,24,32,48),(id,size)
        if not file.exists():
            if args.partial:continue
            raise FileNotFoundError(file)
        source=Image.open(file).convert('RGBA');edges=pipeline.row_edges(source,5)
        rows=[]
        correction=corrections.get(id,{})
        overrides=correction.get('source_rows',{})
        for d in range(5):
            row=source.crop((0,edges[d],source.width,edges[d+1]))
            poses=pipeline.source_poses(row,expected=7 if id=="pen_orange" else 6,minimum=6)[:6]
            if str(d) in overrides:
                replacement=pipeline.source_poses(Image.open(ROOT/overrides[str(d)]).convert('RGBA'),expected=6,minimum=6)
                # Generated rows can have a different source resolution. Match
                # the old row's envelope before the shared native-size scale.
                factor=min(max(p['image'].width for p in poses)/max(p['image'].width for p in replacement),
                           max(p['image'].height for p in poses)/max(p['image'].height for p in replacement))
                for pose in replacement:
                    im=pose['image'];pose['image']=im.resize((max(1,round(im.width*factor)),max(1,round(im.height*factor))),Image.Resampling.NEAREST)
                poses=replacement
            assert len(poses)==6,(id,d,len(poses))
            rows.append(poses)
        scale=min((size-2)/max(p['image'].width for row in rows for p in row),(size-2)/max(p['image'].height for row in rows for p in row))
        native=[]
        for d,row in enumerate(rows):
            frames=[]
            for p,pose in enumerate(row):
                rgba=pose['image'];rgba=rgba.resize((max(1,round(rgba.width*scale)),max(1,round(rgba.height*scale))),Image.Resampling.NEAREST)
                frame=Image.new('RGBA',(size,size));frame.paste(rgba,((size-rgba.width)//2,size-1-rgba.height))
                frame=pipeline.indexed(frame);assert frame.getbbox() and frame.getbbox()[3]<=size-1
                if p in correction.get('horizontal_flip_poses',{}).get(str(d),[]):
                    frame=frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                frames.append(frame)
            # Generation can give identical idle frames after quantization; keep
            # honest counts. Four locomotion poses must remain visibly distinct.
            assert len(set(f.tobytes() for f in frames[2:]))==4,(id,'indistinct run')
            native.append(frames)
        master=Image.new('P',(size*6,size*8));master.putpalette(native[0][0].getpalette())
        for d in range(8):
            frames=native[pipeline.CANON[d]]
            if d>=5:frames=[f.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for f in frames]
            for p,frame in enumerate(frames):master.paste(frame,(p*size,d*size))
        folder=ROOT/'enemies'/id
        if args.check:
            saved=Image.open(folder/(id+'.png'));assert saved.size==master.size and saved.tobytes()==master.tobytes(),id
        else:
            folder.mkdir(parents=True,exist_ok=True)
            master.save(folder/(id+'.png'),bits=4,transparency=0)
            master.convert('RGBA').resize((master.width*4,master.height*4),Image.Resampling.NEAREST).save(folder/(id+'-4x.png'))
        offset=len(raw)//4
        for row in native:
            for frame in row:raw.extend(pipeline.pack(frame,pieces(size)))
        icon=native[4][0]
        icon_size=min(size,32)
        if icon_size!=size:icon=icon.resize((icon_size,icon_size),Image.Resampling.NEAREST)
        icon_data=pipeline.pack(icon,[(0,0,icon_size,icon_size)])
        enemy_index=14 if id=='boss' else catalog.index(e)
        icons[enemy_index*512:(enemy_index+1)*512]=icon_data+bytes(512-len(icon_data))
        tiles=size*size//64
        definitions.append((offset,tiles*8,size,tiles))
        flips=correction.get('horizontal_flip_poses',{})
        row_report={**e,'source_horizontal_flip_rows':[int(d) for d,poses in flips.items() if poses==list(range(6))],'source_horizontal_flip_poses':flips,'source_row_overrides':{d:{'path':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()} for d,path in overrides.items()},'size':size,'frames':30,'hardware_pieces':len(pieces(size)),'tiles_per_frame':tiles,'bytes_per_frame':tiles*32,'rom_offset':offset*4,'rom_bytes':30*tiles*32,'scale':scale,'source_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'native_sha256':hashlib.sha256((folder/(id+'.png')).read_bytes()).hexdigest(),'source_rows':edges,'unique_poses_per_direction':[[len(set(f.tobytes() for f in row[:2])),len(set(f.tobytes() for f in row[2:]))] for row in native]}
        report.append(row_report);print(id,size,tiles,len(raw),flush=True)
    if not args.check:
        (ROOT/'validation/export.json').write_text(json.dumps(report,indent=2)+'\n')
        (ROOT/'palette.json').write_text(json.dumps(pipeline.PALETTE,indent=2)+'\n')
    if len(report)!=13:return
    header='// Generated by art/cangaco-insects-sized-v3/export_sprites.py\n#ifndef ENEMY_ASSET_LAYOUT_H\n#define ENEMY_ASSET_LAYOUT_H\n#include <genesis.h>\n'
    header+='typedef struct {u32 offset;u16 words;u8 size,tiles;} EnemyArt;\n'
    header+=f'#define ENEMY_ASSET_LONGWORDS {len(raw)//4}\n'
    header+='static const EnemyArt ENEMY_ART[15]={\n'
    for i in range(15):
        data=(0,0,24,9) if i in (12,13) else definitions[12 if i==14 else i]
        header+='    {%d,%d,%d,%d},\n'%data
    header+='};\n#endif\n'
    if args.check:
        assert (GAME/'src/system/video/enemy_asset_layout.h').read_text()==header
        assert (GAME/'res/insects/frames.bin').read_bytes()==raw
        assert (GAME/'res/insects/icons.bin').read_bytes()==icons
    else:
        (GAME/'src/system/video/enemy_asset_layout.h').write_text(header)
        (GAME/'res/insects/frames.bin').write_bytes(raw)
        (GAME/'res/insects/icons.bin').write_bytes(icons)
        (ROOT/'runtime').mkdir(exist_ok=True);(ROOT/'runtime/frames.bin').write_bytes(raw)
    print('Verified' if args.check else 'Integrated',len(raw),'bytes')
if __name__=='__main__':main()
