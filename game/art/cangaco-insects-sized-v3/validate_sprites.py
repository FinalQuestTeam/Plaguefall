"""Validate native sizes, shared palette, packing, hardware limits and combat."""
from pathlib import Path
from PIL import Image
import json,re,subprocess,sys,hashlib
from export_sprites import ROOT,GAME,pipeline,pieces

def main():
    rows=json.loads((ROOT/'validation/export.json').read_text());assert len(rows)==13
    raw=(GAME/'res/insects/frames.bin').read_bytes();offset=0
    references=0
    for entry in rows:
        id,size=entry['id'],entry['size']
        expected=int(re.search(r'\.size\s*=\s*(\d+)',(GAME/'src/enemies/defs'/(id+'.c')).read_text()).group(1));assert size==expected
        file=ROOT/'enemies'/id/(id+'.png');master=Image.open(file)
        assert master.mode=='P' and master.size==(size*6,size*8) and master.info['transparency']==0
        assert file.read_bytes()[24]==4
        assert master.getpalette()[:48]==[v for rgb in pipeline.PALETTE for v in rgb]
        assert set(master.tobytes())<=set(range(16))
        assert set(master.convert('RGBA').getchannel('A').tobytes())=={0,255}
        assert entry['native_sha256']==hashlib.sha256(file.read_bytes()).hexdigest()
        assert entry['rom_offset']==offset
        assert all(v==[2,4] for v in entry['unique_poses_per_direction'])
        for d in range(8):
            for p in range(6):
                cell=master.crop((p*size,d*size,(p+1)*size,(d+1)*size));box=cell.getbbox()
                assert box and box[0]>=1 and box[1]>=1 and box[2]<=size-1 and box[3]<=size-1,(id,d,p,box)
                if d<5:
                    frame=pipeline.pack(cell,pieces(size));assert raw[offset:offset+len(frame)]==frame,(id,d,p)
                    offset+=len(frame)
                else:
                    ref=master.crop((p*size,pipeline.CANON[d]*size,(p+1)*size,(pipeline.CANON[d]+1)*size))
                    assert cell.tobytes()==ref.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
                references+=1
        assert master.crop((0,0,size,size)).tobytes()!=master.crop((0,4*size,size,5*size)).tobytes(),(id,'N/S must differ')
    assert offset==len(raw)==118080
    tests=GAME/'art/cangaco-insects-iso60-v2/tests'
    host=['clang','-std=c99','-Werror=implicit-function-declaration','-I'+str(tests),'-I'+str(GAME/'src')]
    reports={}
    for name,sources in [('runtime',[tests/'runtime_test.c',GAME/'src/system/video/herogfx.c']),('combat',[ROOT/'combat_test.c',*sorted((GAME/'src/enemies/defs').glob('*.c'))])]:
        executable='/private/tmp/redrex-sized-'+name+'-test'
        result=subprocess.run(host+[str(s) for s in sources]+['-o',executable],capture_output=True,text=True);assert result.returncode==0,result.stderr
        result=subprocess.run([executable],capture_output=True,text=True);assert result.returncode==0,result.stderr
        reports[name]=json.loads(result.stdout);(ROOT/'validation'/(name+'.json')).write_text(json.dumps(reports[name],indent=2)+'\n')
    report={'passed':True,'pass_scope':'native_assets_hardware_limits_and_combat','source_tool':'image_gen built-in','enemies':13,'directions':104,'runtime_canonical_frames':390,'frame_references':references,'idle_frames':2,'run_frames':4,'native_sizes':sorted(set(e['size'] for e in rows)),'enemy_animation_rom_bytes':len(raw),'enemy_vram_pool_bytes':320*32,'per_enemy_tiles':{e['id']:e['tiles_per_frame'] for e in rows},'palette_visible_max':15,'transparent_index':0,'raw_sha256':hashlib.sha256(raw).hexdigest(),'runtime':reports['runtime'],'combat':reports['combat'],'camera_review':'Visual elevated-camera review; source and native PNGs checked. No exact 3D camera angle can be certified from these 2D rasters.','projection':'Native enemy square and ground hitbox have identical dimensions; bodies, both projectile pools and chain arcs share VIDEO_HEIGHT_OFFSET=16. Contact/AI coordinates unchanged.'}
    (ROOT/'validation/report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
