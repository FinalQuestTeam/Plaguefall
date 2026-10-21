"""Validate native files, frame counts, registration, tile bytes and real ResComp."""
from pathlib import Path
from PIL import Image
import hashlib,json,re,subprocess
from export_sprites import ROOT,GAME,PALETTE,SELECTED,DIRS,cell,pixels

def decode(raw):
    # Independent reader of the two hardware rectangles, column-major tiles.
    image=Image.new('P',(32,48));cursor=0
    for x0,y0,w,h in [(0,0,32,32),(0,32,32,16)]:
        for tx in range(w//8):
            for ty in range(h//8):
                for row in range(8):
                    for pair in range(4):
                        byte=raw[cursor];cursor+=1
                        x=x0+tx*8+pair*2;y=y0+ty*8+row
                        image.putpixel((x,y),byte>>4);image.putpixel((x+1,y),byte&15)
    assert cursor==768
    return image

def main():
    master=Image.open(ROOT/'parceira/parceira.png')
    compact=Image.open(ROOT/'parceira/parceira-compacta.png')
    raw=(ROOT/'runtime/frames.bin').read_bytes()
    full=(ROOT/'runtime/frames-completos.bin').read_bytes()
    palette=(ROOT/'runtime/palette.bin').read_bytes()
    assert master.size==compact.size==(192,768)
    assert len(raw)==23040 and len(full)==38400 and len(palette)==32
    assert palette==(GAME/'res/heroi/palette.bin').read_bytes()
    reference_palette=[v for rgb in PALETTE for v in rgb]
    assert all(v in pixels.LEVELS for v in reference_palette)
    for f in (ROOT/'parceira').glob('*_opt.png'):f.replace(ROOT/'validation'/f.name)
    native=[]
    for file in sorted((ROOT/'parceira').rglob('*.png')):
        if 'previews' in file.parts:continue
        image=Image.open(file)
        assert image.mode=='P' and image.info['transparency']==0 and file.read_bytes()[24]==4,file
        assert image.getpalette()[:48]==reference_palette,file
        assert set(image.tobytes())<=set(range(16)),file
        assert set(image.convert('RGBA').getchannel('A').tobytes())=={0,255},file
        native.append(str(file.relative_to(ROOT)))
    animations=[]
    for d,direction in enumerate(DIRS):
        directional=Image.open(ROOT/'parceira/directions'/('parceira_'+direction+'.png'))
        assert directional.size==(192,96)
        assert directional.tobytes()==master.crop((0,d*96,192,d*96+96)).tobytes()
        assert directional.crop((128,0,192,48)).getbbox() is None
        assert compact.crop((64,d*96,192,d*96+48)).getbbox() is None
        assert compact.crop((128,d*96+48,192,d*96+96)).getbbox() is None
        frames=[cell(master,d,p) for p in range(10)]
        for p,frame in enumerate(frames):
            box=frame.getbbox()
            assert box and box[0]>=1 and box[1]>=1 and box[2]<=31 and box[3]==47,(direction,p,box)
            if d<5:
                offset=(d*10+p)*768
                assert decode(full[offset:offset+768]).tobytes()==frame.tobytes()
            else:
                expected=cell(master,pixels.CANON[d],p).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                assert frame.tobytes()==expected.tobytes()
        assert len({f.tobytes() for f in frames[:4]})==4,direction
        assert len({f.tobytes() for f in frames[4:]})==6,direction
        runtime=[frames[p] for p in SELECTED]
        assert len({f.tobytes() for f in runtime[:2]})==2
        assert len({f.tobytes() for f in runtime[2:]})==4
        for i,frame in enumerate(runtime):
            row,col=(0,i) if i<2 else (1,i-2)
            expected=compact.crop((col*32,d*96+row*48,col*32+32,d*96+row*48+48))
            assert expected.tobytes()==frame.tobytes()
            if d<5:
                offset=(d*6+i)*768
                assert decode(raw[offset:offset+768]).tobytes()==frame.tobytes()
        feet=[]
        for frame in frames[:4]:
            xs=[x for y in range(42,47) for x in range(32) if frame.getpixel((x,y))]
            feet.append(sum(xs)/len(xs))
        assert max(feet)-min(feet)<1.05,(direction,feet)
        run=runtime[2:]
        deltas=[sum(a!=b for a,b in zip(run[i].tobytes(),run[(i+1)%4].tobytes())) for i in range(4)]
        assert min(deltas)>0
        animations.append({'direction':direction,'full_frames':[4,6],'runtime_frames':[2,4],'feet_baseline':46,'idle_foot_centroid_spread':max(feet)-min(feet),'runtime_loop_pixel_deltas':deltas})
    assert cell(master,0,0).tobytes()!=cell(master,4,0).tobytes(),'distinct N/S'
    # Both the full sheet and compact sheet are compiled with the installed SDK.
    result=subprocess.run(['java','-Djava.awt.headless=true','-jar',str(GAME.parent/'SGDK/bin/rescomp.jar'),str(ROOT/'parceira.res'),str(ROOT/'validation/parceira.s')],capture_output=True,text=True)
    (ROOT/'validation/rescomp.log').write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stdout+result.stderr
    for f in (ROOT/'parceira').glob('*_opt.png'):f.replace(ROOT/'validation'/f.name)
    asm=(ROOT/'validation/parceira.s').read_text()
    for prefix,counts in [('parceira',[4,6]),('parceira_compacta',[2,4])]:
        for i in range(16):
            m=re.search(r'^'+prefix+'_animation'+str(i)+r':\s*\n\s*dc.w\s+(\d+)',asm,re.M)
            assert m and int(m.group(1))>>8==counts[i%2],(prefix,i)
            table=re.search(r'^'+prefix+'_animation'+str(i)+r'_frames:\n((?:\s*dc.l[^\n]*\n)+)',asm,re.M)
            assert table
            for symbol in re.findall(r'dc.l\s+(\w+)',table.group(1)):
                frame=re.search(r'^'+symbol+r':\s*\n\s*dc.w\s+(\d+)',asm,re.M);assert frame,symbol
                assert int(frame.group(1))&255==(6 if prefix=='parceira' else (24 if i%2==0 else 9)),symbol
    binary_result=subprocess.run(['java','-Djava.awt.headless=true','-jar',str(GAME.parent/'SGDK/bin/rescomp.jar'),str(ROOT/'runtime/parceira.res'),str(ROOT/'validation/runtime.s')],capture_output=True,text=True)
    (ROOT/'validation/runtime-rescomp.log').write_text(binary_result.stdout+binary_result.stderr)
    assert binary_result.returncode==0,binary_result.stdout+binary_result.stderr
    binary_asm=(ROOT/'validation/runtime.s').read_text()
    assert 'parceira_frames' in binary_asm and 'parceira_palette' in binary_asm
    parts=[int(n) for n in re.findall(r"Sprite frame '[^']+' - (\d+) VDP sprites",result.stdout)]
    assert parts and max(parts)<=4
    def warm_fraction(image):
        data=[p for p in image.tobytes() if p]
        return sum(p in range(8,14) for p in data)/len(data)
    hero=Image.open(GAME/'art/cangaco-protagonista-iso60-v2/heroi/heroi.png')
    assert warm_fraction(master)>warm_fraction(hero)*1.5
    report={'passed':True,'source_tool':'image_gen built-in','pass_scope':'native_assets_packing_and_ResComp_only','integrated_in_game':False,'native_pngs':native,'cell':[32,48],'master':[192,768],'directional_sheet':[192,96],'directions':DIRS,'full_frame_references':80,'compact_frame_references':48,'runtime_canonical_frames':30,'runtime_rom_frames_bytes':len(raw),'palette_file_bytes':32,'palette_identical_to_Damiao':True,'new_palette_slots_needed':0,'transparent_index':0,'alpha':[0,255],'visible_colors':len(set(master.tobytes())-{0}),'runtime_frame_vram_bytes':768,'runtime_hardware_pieces':[[32,32],[32,16]],'ResComp_auto_optimized_piece_range':[min(parts),max(parts)],'frame_timing_ntsc':{'idle':24,'run':9},'frame_timing_pal':{'idle':20,'run':7},'memory_note':'Asset candidate only; not linked into the ROM. Adding one simultaneously displayed actor needs a live768-byte frame, two manual SAT entries and up to768 bytes per frame change. Actual runtime integration/performance must be measured separately.','red_brown_visible_fraction':warm_fraction(master),'Damiao_red_brown_visible_fraction':warm_fraction(hero),'native_sha256':hashlib.sha256((ROOT/'parceira/parceira.png').read_bytes()).hexdigest(),'compact_binary_sha256':hashlib.sha256(raw).hexdigest(),'animations':animations}
    (ROOT/'validation/report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('native_pngs','animations')},indent=2))
if __name__=='__main__':main()
