"""Phase15 shares phase14 modules and generators; native radio antenna and ignition."""
from pathlib import Path
import argparse, hashlib, io, json, math, struct
import numpy as np
from PIL import Image, ImageDraw
from build_phase14_shipyard import PALETTE, SIZE, BOUNDS, START, MACHINES, SOLIDS as POWER_SOLIDS
from campaign_geometry import validate
from phase14_energy import conduits, CONNECTIONS

G=Path(__file__).resolve().parents[1]
A=G/'art/phase15-shipyard-v2'
S=G/'art/phase14-shipyard-v2'
HOT=G/'art/campaign-pattern-v2/launch/source/15-16-shipyard-ignition.png'
CORE=G/'art/phase15-radio-core-proposal-v1/radio-core-native-48x64.png'
ANTENNA_POSITION=(232,256)
BASE=(240,304,32,16)
SOLIDS=[list(BASE),*POWER_SOLIDS[2:]]
RADIO=(256,312)
TARGET=(BASE[0]+BASE[2]//2,BASE[1]+BASE[3]//2)

def export(check=False):
    def emit(p,data):
        if check:assert p.exists() and p.read_bytes()==data,('stale phase15 export',p)
        else:
            p.parent.mkdir(parents=True,exist_ok=True)
            if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
    def png(p,im):
        b=io.BytesIO();im.save(b,format='PNG');emit(p,b.getvalue())
    def js(p,d):emit(p,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
    def ca(name,kind,values):
        fmt='0x%08XUL' if kind=='u32' else '%d'
        align=' __attribute__((aligned(32)))' if kind=='u32' else ''
        return 'static const '+kind+' '+name+'[]'+align+'={\n'+''.join(','.join(fmt%v for v in values[i:i+8])+',\n' for i in range(0,len(values),8))+'};\n'
    palette=sum(map(list,PALETTE),[])+[0]*720;colors=np.array(PALETTE,dtype=np.int32)
    def quant(im):
        rgb=np.array(im.convert('RGB'),dtype=np.int32)
        out=Image.fromarray(((rgb[:,:,None,:]-colors[None,None,:,:])**2).sum(3).argmin(2).astype('uint8'));out.putpalette(palette);return out
    room=Image.new('P',SIZE);room.putpalette(palette)
    floor=Image.open(S/'modules/iron-floor-plate.png')
    for y in range(0,SIZE[1],64):
        for x in range(0,SIZE[0],64):room.paste(floor,(x,y))
    room.paste(Image.open(S/'upper.png'),(0,0));room.paste(Image.open(S/'lower.png'),(0,496))
    for name,x in [('left',0),('right',480)]:
        part=Image.open(S/f'modules/{name}-boundary.png')
        for y in range(112,496,64):room.paste(part.crop((0,0,32,min(64,496-y))),(x,y))
    routes=[
        ('station-1','console',[(80,160),(136,160),(136,304),(240,304)]),
        ('station-2','console',[(432,160),(352,160),(352,304),(264,304)]),
        ('station-3','console',[(384,280),(352,280),(352,312),(264,312)]),
        ('console','battery',[(256,312),(256,432)]),
        *CONNECTIONS[4:],
    ]
    cables,_,energy=conduits(SIZE,PALETTE,routes);room.paste(quant(cables),(0,0),cables.getchannel('A'))
    png(A/'connections.png',cables)
    battery=Image.open(S/'objects/tank-island.png').convert('RGBA');room.paste(quant(battery),(208,416),battery.getchannel('A'))
    native=Image.open(CORE).convert('RGBA');assert native.size==(48,64)
    mask=native.getchannel('A');assert set(mask.tobytes())=={0,255}
    # Keep the approved native pixels. PAL1 already supplies cyan, steel and
    # brass; index11 is opaque black, while index0 remains transparent.
    object_words=struct.unpack('>16H',(G/'res/insects/palette.bin').read_bytes())
    object_colors=np.array([(round((w>>1&7)*255/7),round((w>>5&7)*255/7),round((w>>9&7)*255/7)) for w in object_words],dtype=np.int32)
    object_palette=object_colors.flatten().tolist()+[0]*720
    rgb=np.array(native)[:,:,:3].astype(np.int32)
    pixels=((rgb[:,:,None,:]-object_colors[None,None,1:,:])**2).sum(3).argmin(2).astype('uint8')+1
    pixels[np.array(mask)==0]=0
    antenna=Image.fromarray(pixels);antenna.putpalette(object_palette)
    antenna.info['transparency']=0;png(A/'objects/radio-antenna.png',antenna)
    # The whole transparent prop lives in BG_A, not baked into the floor.
    # This permits correct foreground/background ordering under the mast.
    # All energy terminals enter physical, opaque equipment rather than air.
    for r in energy['routes']:
        for name,p in [(r['source'],r['points'][0]),(r['target'],r['points'][-1])]:
            if name=='console':
                u,v=p[0]+3-ANTENNA_POSITION[0],p[1]+3-ANTENNA_POSITION[1]
                assert mask.getpixel((u,v)),('antenna terminal outside silhouette',p)
    energy['console_role']='protected radio core';energy['all_antenna_terminals_enter_opaque_equipment']=True
    # Six full48x64 frames share the intact mast and casing. Only the existing
    # screen glyph/indicators change; collisions and damage belong to BASE.
    base=antenna
    signal=(rgb[:,:,2]>140)&(rgb[:,:,1]>rgb[:,:,0]*1.4)&(rgb[:,:,0]<100)&(np.array(mask)>0)
    radio=[]
    for state in range(6):
        values=np.array(base).copy();values[signal]=[6,4,2,7,3,11][state]
        im=Image.fromarray(values);im.putpalette(object_palette)
        im.info['transparency']=0;radio.append(im);png(A/'objects'/f'radio-{state}.png',im)
    sheet=Image.new('RGBA',(288,64))
    for i,im in enumerate(radio):sheet.alpha_composite(im.convert('RGBA'),(i*48,0))
    png(A/'radio-states.png',sheet)
    tiles=[];lookup={};indices=[];visible=[]
    for im in radio:
        for x in range(0,48,8):
            for y in range(0,64,8):
                t=im.crop((x,y,x+8,y+8)).tobytes()
                if t not in lookup:lookup[t]=len(tiles);tiles.append(t)
                indices.append(lookup[t]);visible.append(int(any(t)))
    radio_raw=b''.join(bytes((t[i]<<4)|t[i+1] for i in range(0,64,2)) for t in tiles)
    radio_count=len(tiles)
    header='// Generated phase15/16 compact radio:48x64, six states, PAL1.\n'
    header+=ca('phase15RadioTiles','u32',struct.unpack('>'+str(len(radio_raw)//4)+'I',radio_raw))+ca('phase15RadioMap','u16',indices)+ca('phase15RadioVisible','u8',visible)
    header+='static const ObjectiveArt phase15RadioArt={0,48,48,64};\nstatic const CampaignGroundArt phase15RadioGround={phase15RadioTiles,phase15RadioMap,'+str(radio_count)+'};\n'
    emit(G/'src/system/video/phase15_radio.h',header.encode());emit(A/'native/radio-tiles.bin',radio_raw);emit(A/'native/radio-map.bin',struct.pack('>288H',*indices))
    # Ignition changes only complete authored engine interiors. Architecture,
    # antenna, floor, connections, generators and collisions remain identical.
    hot=quant(Image.open(HOT).convert('RGB').resize((512,384),Image.Resampling.LANCZOS)).crop((56,16,200,96))
    fired=room.copy()
    for xy in [(56,16),(320,16)]:fired.paste(hot,xy)
    images={'normal':room,'fire':fired};banks={};peaks={};maps={}
    for name,im in images.items():
        png(A/f'{name}-native.png',im)
        bank=[];lookup={};mapping=[]
        for y in range(0,576,8):
            for x in range(0,512,8):
                tile=im.crop((x,y,x+8,y+8)).tobytes()
                if tile not in lookup:lookup[tile]=len(bank);bank.append(tile)
                mapping.append(lookup[tile])
        grid=np.array(mapping).reshape(72,64);peak=0
        for y in range(3,48):
            for x in range(25):peak=max(peak,len(np.unique(grid[y:y+26,x:x+41])))
        raw=b''.join(bytes((t[i]<<4)|t[i+1] for i in range(0,64,2)) for t in bank)
        reconstructed=b''.join(b''.join(bank[mapping[(y//8)*64+x//8]][(y%8)*8:(y%8+1)*8] for x in range(0,512,8)) for y in range(576))
        assert reconstructed==im.tobytes(),'phase15 packing changed pixels'
        banks[name]=(len(bank),raw);maps[name]=mapping;peaks[name]=peak
        emit(A/f'native/{name}-tiles.bin',raw);emit(A/f'native/{name}-map.bin',struct.pack('>4608H',*mapping))
        full=im.convert('RGBA')
        for x,y in MACHINES:full.alpha_composite(Image.open(S/'objects/generator-3.png').convert('RGBA'),(x-24,y-40))
        full.alpha_composite(radio[2].convert('RGBA'),ANTENNA_POSITION);png(A/f'{name}-complete.png',full)
    generator_info=json.loads((S/'manifest.json').read_text())['generator'];reserved=generator_info['tiles']+radio_count
    maximum=max(peaks.values());cache=min(640-reserved,math.ceil((maximum+8)/16)*16)
    assert maximum<=cache and cache+reserved<=640,('phase15 cache overflow',peaks,reserved,cache)
    words=[(round(r*7/255)<<1)|(round(g*7/255)<<5)|(round(b*7/255)<<9) for r,g,b in PALETTE]
    emit(A/'native/palette.bin',struct.pack('>16H',*words))
    code='// Generated by tools/build_phase15_shipyard.py; shares phase14 modules.\n'+ca('phase15Palette','u16',words)
    for name,(count,raw) in banks.items():
        code+=ca('phase15_'+name+'Tiles','u32',struct.unpack('>'+str(len(raw)//4)+'I',raw))+ca('phase15_'+name+'Map','u16',maps[name])
        code+=f'static const ArenaStream phase15_{name}Stream={{{count}}};\nstatic const ArenaScene phase15_{name}Scene={{.tiles=phase15_{name}Tiles,.map=phase15_{name}Map,.palette=phase15Palette,.tileCount={cache},.rows=72,.cols=64,.stream=&phase15_{name}Stream,.streamOverlay=TRUE}};\n'
    code+=f'static ArenaScene phase15Scene={{.tiles=phase15_normalTiles,.map=phase15_normalMap,.palette=phase15Palette,.tileCount={cache},.rows=72,.cols=64,.stream=&phase15_normalStream,.streamOverlay=TRUE}};\n'
    code+='static bool CL15_sceneReset(void){const bool changed=phase15Scene.map!=phase15_normalMap;phase15Scene=phase15_normalScene;return changed;}\nstatic void CL15_sceneFire(void){phase15Scene=phase15_fireScene;}\n'
    code+='static const ArenaRect phase15Solids[]={'+','.join('{'+','.join(map(str,r))+',TRUE}' for r in SOLIDS)+'};\n'
    code+='const ArenaDef CAMPAIGN_LAUNCH_RADIO={'+','.join(map(str,[*SIZE,*BOUNDS,*START]))+',phase15Solids,'+str(len(SOLIDS))+',&phase15Scene};\n'
    emit(G/'src/levels/campaign_launch_phase15.inc',code.encode())
    header='// Generated compact radio anchors; collision and damage share BASE.\n#ifndef PHASE15_LAYOUT_H\n#define PHASE15_LAYOUT_H\n'
    for name,value in dict(RADIO_X=RADIO[0],RADIO_Y=RADIO[1],BASE_X=BASE[0],BASE_Y=BASE[1],BASE_W=BASE[2],BASE_H=BASE[3],TARGET_X=TARGET[0],TARGET_Y=TARGET[1],NPC_X=TARGET[0]-12,NPC_Y=TARGET[1]-12).items():header+=f'#define PHASE15_{name} {value}\n'
    header+='#endif\n'
    emit(G/'src/levels/phase15_layout.h',header.encode())
    d=dict(size=list(SIZE),bounds=BOUNDS,start=START,solids=SOLIDS,points=[],machines=MACHINES,antenna_position=list(ANTENNA_POSITION),radio=list(RADIO),protected_station_footprint=SOLIDS[0],target=list(TARGET),mast_has_collision=False,mast_receives_damage=False,objective_seconds=120,generators_powered_on_entry=True,native_pixel_block=1,energy=energy,geometry=validate(dict(bounds=BOUNDS,start=START,solids=SOLIDS,points=[])),generator=generator_info,radio_art=dict(size=[48,64],frames=6,tiles=radio_count,palette='PAL1'),memory=dict(cache_tiles=cache,source_tiles={k:v[0] for k,v in banks.items()},maximum_visible_patterns=peaks,generator_tiles=generator_info['tiles'],radio_tiles=radio_count,total_resident_tiles=cache+reserved,heap_bytes={k:(v[0]+cache*4)*2 for k,v in banks.items()},lossy_tile_replacements=0),ignition_changes_only_engine_interiors=True)
    d['sources']=[dict(path=str(p.relative_to(G)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [S/'manifest.json',CORE,G/'res/insects/palette.bin',HOT]]
    js(A/'manifest.json',d);return d

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();print(json.dumps(export(args.check)['memory'],indent=2))
