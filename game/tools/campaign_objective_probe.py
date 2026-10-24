"""Read-only libretro probes: exact compacted objective residency and ground tiles."""
import json,re,struct

def inspect_objectives(game,read,vram,syms,camera_x,camera_y,bga_addr):
    meta=json.loads((game/'art/objective-sprites-v1/assets.json').read_text())['assets']
    binary=(game/'res/objectives/animations.bin').read_bytes()
    header=(game/'src/system/video/campaign_ground_art.h').read_text()
    bases=struct.unpack('>10H',read(syms['objectiveArtBases'][0],20));resident=[];ranges=[]
    def vb(address,n):return bytes(vram[((address+i)&65535)^1] for i in range(n))
    def vw(address):return vram[address]+(vram[address+1]<<8)
    for art,base in enumerate(bases):
        if not base:continue
        name=meta[art]['name'];prefix='campaign'+name.capitalize()
        found=re.search(r'static const u32 '+prefix+r'Tiles\[\]=\{(.*?)\};',header,re.S)
        if found:
            data=b''.join(struct.pack('>I',int(x,16)) for x in re.findall(r'0x([0-9A-Fa-f]+)UL',found[1]))
            indices=[int(x) for x in re.findall(r'\d+',re.search(r'static const u16 '+prefix+r'Map\[\]=\{(.*?)\};',header,re.S)[1])]
            original=binary[meta[art]['offset_words']*4:meta[art]['offset_words']*4+meta[art]['bytes']]
            assert b''.join(data[i*32:i*32+32] for i in indices)==original,('compact map alters original pixels',name)
        else:
            start=meta[art]['offset_words']*4;data=binary[start:start+meta[art]['bytes']]
        assert vb(base*32,len(data))==data,('objective atlas residency mismatch',name,base)
        resident.append({'art':name,'tiles':len(data)//32,'all6frames_pixel_exact':True})
        ranges.append((base,base+len(data)//32,name))
    for a,b in zip(sorted(ranges),sorted(ranges)[1:]):assert a[1]<=b[0],('objective atlases overlap',a,b)
    ground_tiles=0;ground_objects=0
    for slot in range(7):
        x,y,age,art,frame,mode,visible,ground,primed=struct.unpack('>hhH6B',read(syms['objectiveVisuals'][0]+slot*12,12))
        if not visible or not ground or not bases[art]:continue
        m=meta[art];rows=m['height']//8;cols=m['width']//8
        col=(x-m['width']//2)//8;row=(y-m['height']+8)//8;sampled=0
        for xx in range(cols):
            for yy in range(rows):
                wx,wy=col+xx,row+yy
                if not(camera_x//8<=wx<camera_x//8+64 and camera_y//8<=wy<camera_y//8+32):continue
                start=m['offset_words']*4+(frame*m['tiles_per_frame']+xx*rows+yy)*32;expected=binary[start:start+32]
                if not any(expected):continue
                attr=vw(bga_addr+((wy&31)*64+(wx&63))*2)
                assert vb((attr&2047)*32,32)==expected,('ground objective pixels differ',m['name'],slot,frame,wx,wy,attr)
                sampled+=1
        if sampled:ground_objects+=1;ground_tiles+=sampled
    return {'passed':True,'resident':resident,'ground_objects_checked':ground_objects,'ground_tiles_pixel_checked':ground_tiles}
