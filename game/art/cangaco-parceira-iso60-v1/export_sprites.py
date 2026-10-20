"""Technical export only; drawn poses come from image_gen, same pipeline as Rex."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from io import BytesIO
import argparse,hashlib,importlib.util,json,shutil,struct,tempfile
ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[1]
spec=importlib.util.spec_from_file_location('pixels',GAME/'art/cangaco-insects-iso60-v2/export_sprites.py')
pixels=importlib.util.module_from_spec(spec);spec.loader.exec_module(pixels)
PALETTE=json.loads((GAME/'art/cangaco-protagonista-iso60-v2/palette.json').read_text())
pixels.PALETTE=PALETTE
LAYOUT=json.loads((GAME/'res/actor_animation.json').read_text())
SELECTED=LAYOUT['idle_source_poses']+LAYOUT['run_source_poses']
DIRS=pixels.DIRS

def cell(master,d,p):
    row,col=(0,p) if p<4 else (1,p-4)
    return master.crop((col*32,d*96+row*48,col*32+32,d*96+row*48+48))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    def write(path,data):
        if args.check:assert path.read_bytes()==data,path
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    def png(path,image):
        out=BytesIO();image.save(out,format='PNG',bits=4,transparency=0);write(path,out.getvalue())
    with tempfile.TemporaryDirectory(prefix='redrex-parceira-') as directory:
        temporary=Path(directory);(temporary/'originals').mkdir()
        shutil.copyfile(ROOT/'originals/parceira.png',temporary/'originals/parceira.png')
        pixels.ROOT=temporary
        full_raw,_,report=pixels.export({'id':'parceira','family':'hero'})
        generated=temporary/'enemies/parceira'
        master=Image.open(generated/'parceira.png').copy()
    # Focused image_gen correction: NE idle has four planted-feet poses.
    correction=ROOT/'originals/parceira-NE-idle.png'
    poses=pixels.source_poses(Image.open(correction).convert('RGBA'),expected=4,minimum=4)
    ratio=min(30/max(p['image'].width for p in poses),38/max(p['image'].height for p in poses))
    override=[]
    for i,pose in enumerate(poses):
        image=pose['image'];image=image.resize((max(1,round(image.width*ratio)),max(1,round(image.height*ratio))),Image.Resampling.NEAREST)
        image=image.crop(image.getchannel('A').getbbox())
        frame=Image.new('RGBA',(32,48));frame.paste(image,((32-image.width)//2,47-image.height))
        master.paste(pixels.indexed(frame),(i*32,96))
        override.append({'direction':'NE','pose':i,'file':'originals/parceira-NE-idle.png','bounds':pose['bounds'],'scale':ratio})
    running_source=ROOT/'originals/parceira-NE-run.png'
    running_image=Image.open(running_source).convert('RGBA');edges=pixels.row_edges(running_image,2)
    running_poses=[]
    for row in range(2):
        extracted=pixels.source_poses(running_image.crop((0,edges[row],running_image.width,edges[row+1])),expected=3,minimum=3)
        for pose in extracted:
            pose['row_origin']=edges[row];running_poses.append(pose)
    assert len(running_poses)==6
    run_ratio=min(30/max(p['image'].width for p in running_poses),40/max(p['image'].height for p in running_poses))
    for i,pose in enumerate(running_poses):
        image=pose['image'];image=image.resize((max(1,round(image.width*run_ratio)),max(1,round(image.height*run_ratio))),Image.Resampling.NEAREST)
        image=image.crop(image.getchannel('A').getbbox())
        frame=Image.new('RGBA',(32,48));frame.paste(image,((32-image.width)//2,47-image.height))
        master.paste(pixels.indexed(frame),(i*32,144))
        override.append({'direction':'NE','pose':i+4,'file':'originals/parceira-NE-run.png','bounds':pose['bounds'],'row_origin':pose['row_origin'],'scale':run_ratio})
    report['correction_run_source_sha256']=hashlib.sha256(running_source.read_bytes()).hexdigest()
    # Register whole idle poses horizontally to a stable foot reference. No
    # pixels/limbs are drawn; this only compensates source-atlas registration.
    registration=[]
    def foot_x(frame):
        xs=[x for y in range(42,47) for x in range(32) if frame.getpixel((x,y))]
        return sum(xs)/len(xs)
    for d in range(5):
        frames=[cell(master,d,p) for p in range(4)]
        target=sum(foot_x(frame) for frame in frames)/4
        for p,frame in enumerate(frames):
            box=frame.getbbox();dx=max(1-box[0],min(31-box[2],round(target-foot_x(frame))))
            adjusted=Image.new('P',(32,48));adjusted.putpalette(master.getpalette());adjusted.paste(frame,(dx,0))
            master.paste(adjusted,(p*32,d*96))
            registration.append({'direction':DIRS[d],'pose':p,'horizontal_translation':dx,'foot_x':foot_x(adjusted)})
    for d in range(5,8):
        canonical=pixels.CANON[d]
        for p in range(10):
            row,col=(0,p) if p<4 else (1,p-4)
            master.paste(cell(master,canonical,p).transpose(Image.Transpose.FLIP_LEFT_RIGHT),(col*32,d*96+row*48))
    png(ROOT/'parceira/parceira.png',master)
    turn=Image.new('P',(256,48));turn.putpalette(master.getpalette())
    for d in range(8):
        png(ROOT/'parceira/directions'/('parceira_'+DIRS[d]+'.png'),master.crop((0,d*96,192,d*96+96)))
        turn.paste(cell(master,d,0),(d*32,0))
    png(ROOT/'parceira/parceira_turntable.png',turn)
    full_raw=bytearray()
    for d in range(5):
        for p in range(10):full_raw.extend(pixels.frame_bytes(cell(master,d,p)))
    report['source_overrides']=override
    report['correction_source_sha256']=hashlib.sha256(correction.read_bytes()).hexdigest()
    report['idle_registration']=registration
    compact=Image.new('P',master.size);compact.putpalette(master.getpalette())
    compact_raw=bytearray()
    for d in range(8):
        sheet=Image.new('P',(192,96));sheet.putpalette(master.getpalette())
        for i,p in enumerate(SELECTED):
            image=cell(master,d,p);col,row=(i,0) if i<2 else (i-2,1)
            sheet.paste(image,(col*32,row*48))
            if d<5:compact_raw.extend(pixels.frame_bytes(image))
        compact.paste(sheet,(0,d*96))
        png(ROOT/'parceira/directions'/('parceira_'+DIRS[d]+'_compacta.png'),sheet)
    png(ROOT/'parceira/parceira-compacta.png',compact)
    palette=b''.join(struct.pack('>H',(round(r/255*7)<<1)|(round(g/255*7)<<5)|(round(b/255*7)<<9)) for r,g,b in PALETTE)
    write(ROOT/'runtime/frames.bin',compact_raw)
    write(ROOT/'runtime/frames-completos.bin',full_raw)
    write(ROOT/'runtime/palette.bin',palette)
    times='['+''.join('[24,24][9,9,9,9]' for _ in range(8))+']'
    resource='SPRITE parceira "parceira/parceira.png" 4 6 FAST 6 NONE BALANCED FAST\n'
    resource+='SPRITE parceira_compacta "parceira/parceira-compacta.png" 4 6 FAST '+times+' NONE BALANCED FAST\n'
    write(ROOT/'parceira.res',resource.encode())
    write(ROOT/'runtime/parceira.res',b'BIN parceira_frames "frames.bin" 4\nBIN parceira_palette "palette.bin" 2\n')
    write(ROOT/'palette.json',(json.dumps(PALETTE,indent=2)+'\n').encode())
    write(ROOT/'palette.gpl',('GIMP Palette\nName: RedRex parceira shared Rex PAL2\nColumns: 4\n#\n'+'\n'.join(f'{r} {g} {b} index{i}' for i,(r,g,b) in enumerate(PALETTE))+'\n').encode())
    report.update({'native_master_sha256':hashlib.sha256((ROOT/'parceira/parceira.png').read_bytes()).hexdigest(),'native_cell':[32,48],'full_animation':{'idle':4,'run':6},'runtime_selected_poses':SELECTED,'runtime_animation':{'idle':2,'run':4},'runtime_canonical_frames':30,'runtime_bytes':len(compact_raw),'palette_shared_with':'heroi PAL2','source_tool':'image_gen built-in','technical_adjustments':'alpha segmentation, crop, registration, nearest-neighbour scaling, palette indexing; same algorithm and feet baseline46 as Rex; no procedural drawing'})
    write(ROOT/'validation/export.json',(json.dumps(report,indent=2)+'\n').encode())
    if not args.check:previews(master)
    print(json.dumps({k:v for k,v in report.items() if k!='cells'},indent=2))

def previews(master):
    folder=ROOT/'previews';folder.mkdir(exist_ok=True)
    turn=Image.open(ROOT/'parceira/parceira_turntable.png').convert('RGBA')
    (ROOT/'parceira/previews').mkdir(exist_ok=True)
    turn.resize((1024,192),Image.Resampling.NEAREST).save(ROOT/'parceira/previews/turntable-4x.png')
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
    for name,poses,duration in [('repouso',[0,2],400),('corrida',[4,6,7,9],150),('repouso-completo',list(range(4)),200),('corrida-completa',list(range(4,10)),100)]:
        frames=[]
        for p in poses:
            canvas=Image.new('RGB',(1024,224),(24,24,36));draw=ImageDraw.Draw(canvas)
            for d,label in enumerate(DIRS):
                draw.text((d*128+52,4),label,font=font,fill=(219,219,182))
                image=cell(master,d,p).convert('RGBA').resize((128,192),Image.Resampling.NEAREST)
                canvas.paste(image,(d*128,32),image)
            frames.append(canvas)
        frames[0].save(folder/('parceira-'+name+'-4x.png'))
        frames[0].save(folder/('parceira-'+name+'-4x.gif'),save_all=True,append_images=frames[1:],duration=duration,loop=0,disposal=2)
    # Full canonical contact sheet, separate from the native spritesheet.
    contact=Image.new('RGB',(1280,5*212),(24,24,36));draw=ImageDraw.Draw(contact)
    for d,label in enumerate(DIRS[:5]):
        draw.text((4,d*212),label,font=font,fill=(219,219,182))
        for p in range(10):
            image=cell(master,d,p).convert('RGBA').resize((128,192),Image.Resampling.NEAREST)
            contact.paste(image,(p*128,d*212+20),image)
    contact.save(folder/'parceira-todas-poses-4x.png')
    hero=Image.open(GAME/'art/cangaco-protagonista-iso60-v2/heroi/heroi.png')
    compare=Image.new('RGB',(1024,448),(24,24,36));draw=ImageDraw.Draw(compare)
    for row,(actor,label) in enumerate([(hero,'REX'),(master,'PARCEIRA')]):
        draw.text((4,row*224),label,font=font,fill=(219,219,182))
        for d,direction in enumerate(DIRS):
            image=cell(actor,d,0).convert('RGBA').resize((128,192),Image.Resampling.NEAREST)
            compare.paste(image,(d*128,row*224+32),image)
    compare.save(folder/'rex-parceira-comparacao-4x.png')

if __name__=='__main__':main()
