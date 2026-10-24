"""Prepare reproducible visual evidence from existing emulator captures/videos.
No game code or art is changed; montage generation is for inspection only.
"""
from pathlib import Path
import json,hashlib,struct,subprocess,shutil,os
from PIL import Image,ImageDraw
A=Path(__file__).resolve().parent;G=A.parents[1];BASE=G/'art/campaign-integrated-v1';WHOLE=G/'art/campaign-whole-scenes-v1'
(A/'frames').mkdir(exist_ok=True);(A/'maps').mkdir(exist_ok=True)
summary=json.loads((BASE/'summary.json').read_text());review=json.loads((WHOLE/'review-data.json').read_text());native={s['phase']:WHOLE/s['native'] for s in review['stages']}
rom=G/'out/release/Plaguefall.bin';sha=hashlib.sha256(rom.read_bytes()).hexdigest();assert summary['rom_sha256']==sha
# Decode approved map banks for1/2/5 rather than using a generated illustration.
def decode(folder,width,filename='map.bin'):
 data=(folder/'tiles.bin').read_bytes();raw=(folder/filename).read_bytes();mp=struct.unpack('>'+str(len(raw)//2)+'H',raw);pal=struct.unpack('>16H',(folder/'palette.bin').read_bytes());colors=[tuple(((v>>sh)&7)*255//7 for sh in (1,5,9)) for v in pal]
 out=Image.new('RGB',(width,len(mp)//(width//8)*8))
 for n,v in enumerate(mp):
  data8=data[(v&2047)*32:(v&2047)*32+32];patch=Image.new('RGB',(8,8));patch.putdata([colors[c] for b in data8 for c in (b>>4,b&15)])
  if v&0x800:patch=patch.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  if v&0x1000:patch=patch.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  out.paste(patch,(n%(width//8)*8,n//(width//8)*8))
 return out
for phase,folder,width in [('1',G/'res/courtyard',512),('2A',G/'res/courtyard',512),('2B',G/'art/campaign-early-v1/church_ruins',512),('5',G/'art/campaign-early-v1/signal',384)]:
 p=A/'maps'/f'{phase}.png';decode(folder,width).save(p);native[phase]=p
rows=[]
for s in summary['stages']:
 phase=s['phase'];group=s['group'];m=s['measurements']['ntsc'];p=BASE/m['image'];frames=[]
 def copy(src,label):
  dst=A/'frames'/f'{phase}-{label}.png';shutil.copy2(src,dst);frames.append(dict(label=label,path=str(dst.relative_to(A)),source=str(src.relative_to(G)),method='existing emulator PNG',sha256=hashlib.sha256(src.read_bytes()).hexdigest()))
 copy(p,'ntsc-entry')
 if group=='escorts':
  stem=p.stem.replace('-entrada','');copy(p.with_name(stem+'-meio.png'),'ntsc-middle');copy(p.with_name(stem+'-saida.png'),'ntsc-end')
 elif phase=='9':copy(p.with_name('9-camera-middle.png'),'ntsc-middle');copy(p.with_name('9-camera-exit.png'),'ntsc-end')
 else:
  movie=BASE/m['movie'];duration=float(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(movie)],text=True))
  for label,t in [('ntsc-middle',min(6,duration*.35)),('ntsc-action',min(12,duration*.7))]:
   dst=A/'frames'/f'{phase}-{label}.png';subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-ss',str(t),'-i',str(movie),'-frames:v','1',str(dst)],check=True)
   frames.append(dict(label=label,path=str(dst.relative_to(A)),source=str(movie.relative_to(G)),method='recorded emulator video frame',time_seconds=round(t,3)))
 copy(BASE/s['measurements']['pal']['image'],'pal-entry')
 extra=[]
 if phase=='3':extra.append(p.with_name('03-church-ruined.png'))
 if phase=='15':extra.append(p.with_name('15-ignition.png'))
 if phase=='6B':extra.extend(sorted(p.parent.glob('06b-portao-*.png')))
 for i,p2 in enumerate(extra):copy(p2,'special-'+str(i))
 d=dict(phase=phase,name=s['name'],goal=s['goal'],group=group,native=os.path.relpath(native[phase],A),frames=frames)
 rows.append(d)
# Full size gameplay contact sheets, four views per variant.
for start in range(0,len(rows),5):
 chunk=rows[start:start+5];sheet=Image.new('RGB',(1280,len(chunk)*248),(20,26,24));dr=ImageDraw.Draw(sheet)
 for y,row in enumerate(chunk):
  for x,f in enumerate(row['frames'][:4]):
   dr.text((x*320+6,y*248+4),'FASE '+row['phase']+' / '+f['label'],fill=(245,211,144));im=Image.open(A/f['path']).convert('RGB').resize((320,224),Image.Resampling.NEAREST);sheet.paste(im,(x*320,y*248+24))
 sheet.save(A/f'contact-{start//5+1}.png')
# Whole maps are available individually in the audit viewer, retaining aspect.
report=dict(rom_sha256=sha,scope='19 campaign variants, all phases including approved1/2/5; review only, no runtime/art mutation',method='Whole native maps, NTSC entry/movement/action or route middle/end; PAL entry; cinematic/branch special states. Visual conclusions are manual design judgments, not automatic pixel scores.',variants=rows)
(A/'evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Prepared',len(rows),'variants;',sum(len(r['frames']) for r in rows),'frames; ROM',sha)
