"""Build an isolated data-only ROM candidate, leaving all production files intact.
Existing code/layout addresses stay fixed. A new constant obstacle table is
appended, and the phase1 arena points to it. This is NOT a campaign release.
"""
from pathlib import Path
import json,struct,hashlib,subprocess,shutil
A=Path(__file__).resolve().parent;G=A.parents[1]
m=json.loads((A/'manifest.json').read_text());raw=(G/'out/release/rom.bin').read_bytes()
assert hashlib.sha256(raw).hexdigest()==m['production_rom_sha256']
symbols={}
for line in subprocess.check_output(['/opt/homebrew/bin/m68k-elf-nm','-Sn',str(G/'out/release/rom.out')],text=True).splitlines():
    v=line.split()
    if len(v)>=3:symbols[v[-1]]=int(v[0],16)
data=bytearray(raw);changes=[]
for symbol,filename,size in [('courtyard_tiles','tiles.bin',20480),('courtyard_map','map.bin',6144),('courtyard_damaged','damaged.bin',6144),('courtyard_palette','palette.bin',32)]:
    buf=(A/'native'/filename).read_bytes();assert len(buf)<=size
    addr=symbols[symbol];data[addr:addr+size]=buf+bytes(size-len(buf));changes.append(dict(symbol=symbol,address=addr,allocated_bytes=size,payload_bytes=len(buf)))
arena=symbols['COURTYARD_arena'];assert struct.unpack_from('>HH',data,arena)==(512,384)
original_solids=struct.unpack_from('>I',data,arena+16)[0]
assert data[arena+20]==2 and len(data[arena:arena+26])==26
while len(data)%4:data.append(255)
solid_addr=len(data)
for x,y,w,h,shots in m['solids']:data.extend(struct.pack('>hhhhBB',x,y,w,h,int(shots),0))
struct.pack_into('>hhhh',data,arena+4,*m['bounds'])
struct.pack_into('>I',data,arena+16,solid_addr);data[arena+20]=len(m['solids'])
while len(data)%256:data.append(255)
for addr in (0x120,0x150):data[addr:addr+48]=b'PLAGUEFALL - PATTERN PHASE 01'.ljust(48,b' ')
struct.pack_into('>I',data,0x1a4,len(data)-1)
data[0x18e:0x190]=bytes(2);check=0
for i in range(0,len(data),2):check^=int.from_bytes(data[i:i+2],'big')
struct.pack_into('>H',data,0x18e,check)
dest=A/'rom';dest.mkdir(exist_ok=True)
for name in ('rom.bin','Plaguefall-Phase01-Pattern.bin'):(dest/name).write_bytes(data)
shutil.copy2(G/'out/release/rom.out',dest/'rom.out')
result=dict(method='Isolated data-only prototype; existing code addresses unchanged; source ELF used only for stable code/RAM symbol addresses.',production_rom_unchanged=True,production_rom_sha256=m['production_rom_sha256'],prototype_rom_sha256=hashlib.sha256(data).hexdigest(),prototype_rom_bytes=len(data),resource_replacements=changes,arena_address=arena,old_solid_table=original_solids,new_solid_table=solid_addr,bounds=m['bounds'],solids=m['solids'],limitations=['Fase1 é a única fase validada deste protótipo; recursos da igreja também são compartilhados por outras fases, que não estão aprovadas nesta ROM.','A ROM de produção e os recursos/C originais permanecem intactos.','O banco de cena mantém a reserva original640tiles;638são utilizados no protótipo.'])
(A/'rom/manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
assert hashlib.sha256((G/'out/release/rom.bin').read_bytes()).hexdigest()==m['production_rom_sha256']
print(json.dumps({k:result[k] for k in ('prototype_rom_sha256','prototype_rom_bytes','bounds')},indent=2))
