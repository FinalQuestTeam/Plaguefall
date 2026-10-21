"""Review-only UI compositions using production captures and the existing font.

Writes only this proposal folder. No game code, resource export or ROM build.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, html

ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[1]
FONT=Image.open(GAME.parent/'SGDK/res/image/font_default.png')
SOURCE=GAME/'art/routemap-regional-v1/validation/ntsc'
BLACK=(0,0,0)
INK=(32,32,32)
# Match the actual captured emulator palette, including the shared font ink.
CREAM=(238,238,205)
GOLD=(238,206,65)

def label(im,x,y,s,color=CREAM):
 assert x>=8 and x+len(s)*8<=312,(s,len(s),x)
 assert y%8==0 and y+8<=216,(s,y)
 for i,c in enumerate(s):
  g=ord(c)-32;assert 0<=g<96
  glyph=FONT.crop((g%16*8,g//16*8,g%16*8+8,g//16*8+8)).convert('L')
  im.paste(color,(x+i*8,y),glyph.point(lambda v:255 if v else 0))

def propose(case):
 im=Image.open(SOURCE/case['capture']).convert('RGB')
 assert im.size==(320,224)
 ImageDraw.Draw(im).rectangle((0,176,319,223),fill=INK)
 # Preserve the original map header, without adding an AGORA label.
 label(im,((40-len(case['name']))//2)*8,176,case['name'],GOLD)
 label(im,((40-len(case['cause']))//2)*8,184,case['cause'])
 label(im,((40-len(case['consequence']))//2)*8,192,case['consequence'])
 # Empty tile row separates explanation and action. Bottom row stays clear.
 action='A / START: SEGUIR PARA A FASE '+case['next']
 label(im,312-len(action)*8,208,action,GOLD)
 return im

def main():
 data=json.loads((ROOT/'proposta.json').read_text())
 frames=[]
 for case in data['cases']:
  frame=propose(case);frame.save(ROOT/('proposta-'+case['id']+'.png'))
  frame.resize((960,672),Image.Resampling.NEAREST).save(ROOT/('proposta-'+case['id']+'-3x.png'))
  frames.append(frame)
 # Two screenshots, same pixel scale, showing the current and proposed UI.
 before=Image.open(SOURCE/data['cases'][0]['capture']).convert('RGB')
 board=Image.new('RGB',(1320,530),'#101719');d=ImageDraw.Draw(board)
 font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',23)
 d.text((16,12),'ATUAL',font=font,fill='#b9ae96')
 d.text((674,12),'PROPOSTA PARA APROVAR',font=font,fill='#ffbf57')
 board.paste(before.resize((640,448),Image.Resampling.NEAREST),(16,51))
 board.paste(frames[0].resize((640,448),Image.Resampling.NEAREST),(674,51))
 d.text((16,507),'Captura da ROM atual',font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16),fill='#b9ae96')
 d.text((674,507),'Composição de interface • ROM não alterada',font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16),fill='#b9ae96')
 board.save(ROOT/'antes-depois.png')
 # Same proposal during travel: distinct command matches the actual behavior.
 travel=frames[0].copy();ImageDraw.Draw(travel).rectangle((0,208,319,223),fill=INK)
 action='A / START: PULAR VIAGEM'
 label(travel,312-len(action)*8,208,action,GOLD)
 travel.save(ROOT/'durante-viagem.png')
 report={'proposalOnly':True,'cases':len(frames),'screen':[320,224],'font':[8,8],
  'maxCharacters':max(len(s) for c in data['cases'] for s in (
   c['name'],c['cause'],c['consequence'],
   'A / START: SEGUIR PARA A FASE '+c['next'])),
  'allTextsWithin38Columns':True,'bottomMargin':8,'sourceArtUnchanged':True,
  'destinationPrefixRemoved':True,'currentHeaderUnchanged':True,'bodyAlignment':'centered_on_tile_grid','actionAlignment':'right','travelActionRightMargin':8,
  'paletteNote':'Two font color palettes: PAL0 ivory / PAL3 gold. No new font tiles needed; proposal only.'}
 (ROOT/'validacao-layout.json').write_text(json.dumps(report,indent=2)+'\n')
 items=[]
 for c in data['cases']:
  items.append({'id':c['id'],'label':c['label'],'next':c['next'],'name':c['name'],
   'cause':c['cause'],'consequence':c['consequence'],'capture':'../routemap-regional-v1/validation/ntsc/'+c['capture'],
   'proposal':'proposta-'+c['id']+'.png'})
 buttons=''.join(f'<button data-case="{i}" aria-pressed="{str(i==0).lower()}">{html.escape(c["label"])}</button>' for i,c in enumerate(items))
 page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mapa — proposta de UX do rodapé</title>
<style>:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#101719;color:#f2dfc0;font:17px/1.6 system-ui,sans-serif}main{max-width:1400px;padding:32px 24px 65px;margin:auto}.tag{color:#ffbf57;font-size:12px;letter-spacing:.12em}h1{font-size:40px;line-height:1.15;margin:12px 0}h2{font-size:24px}p{color:#b9ae96;max-width:1000px}.status{display:inline-block;border:1px solid #776447;border-radius:20px;color:#ffbf57;font-size:13px;padding:6px 12px;margin:8px 0}nav{display:flex;gap:8px;flex-wrap:wrap;margin:22px 0 18px}button{font:inherit;font-size:14px;cursor:pointer;border:1px solid #475256;background:#1a2426;color:#f2dfc0;padding:8px 12px;border-radius:6px}button[aria-pressed=true]{background:#ffbf57;color:#101719}.comparison{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.panel{min-width:0}.panel h2{margin:0 0 10px;font-size:18px}.panel img{width:100%;height:auto;image-rendering:pixelated;border:1px solid #475256}.panel.proposal{color:#ffbf57}.copy{margin-top:26px;display:grid;grid-template-columns:1fr 1fr;gap:20px}.card{background:#182225;border:1px solid #354347;border-radius:8px;padding:20px}.card p{margin:5px 0}.card strong{color:#ffbf57}.copy>.card:first-child{text-align:center}.copy #action{text-align:right}.card ol{padding-left:20px;color:#b9ae96}.card li{margin-bottom:8px}.native{display:flex;gap:24px;align-items:flex-start;flex-wrap:wrap;margin-top:28px}.native img{width:320px;height:224px;image-rendering:pixelated;border:1px solid #475256}.native p{max-width:600px}.travel{display:block;width:640px;max-width:100%;image-rendering:pixelated;margin-left:0;margin-right:auto}a{color:#ffbf57}footer{border-top:1px solid #475256;margin-top:34px;padding-top:20px;font-size:14px}@media(max-width:720px){main{padding:24px 16px}.comparison,.copy{grid-template-columns:1fr}h1{font-size:30px}}
</style><main><div class="tag">PLAGUEFALL / UX DO MAPA / PROPOSTA 01</div><h1>Destino, motivo, ação.</h1><span class="status">Para aprovação • A ROM permanece igual</span><p>O rodapé começa diretamente pelo nome da fase, seguido do resultado e da consequência da rota. Sem “AGORA” no cabeçalho e sem o prefixo “PRÓXIMA: 10A —”. O nome da fase e as explicações ficam centralizados. O comando de pular viagem fica alinhado à direita, com margem de 8 px.</p><nav aria-label="Cenários para avaliar">'''+buttons+'''</nav>
<div class="comparison"><section class="panel"><h2>Atual — captura da ROM</h2><img id="before" src="../routemap-regional-v1/validation/ntsc/map-9-10A.png" alt="Rodapé atual: origem, destino e consequência com o mesmo destaque"></section><section class="panel proposal"><h2>Proposta — composição para aprovação</h2><img id="after" src="proposta-10a.png" alt="Proposta do rodapé: somente nome da fase, texto centralizado e comando alinhado à direita"></section></div>
<div class="copy"><section class="card"><strong id="destination">ACESSO DOS TÉCNICOS</strong><p id="cause">Você saiu sem sofrer dano.</p><p id="consequence">O acesso dos técnicos foi liberado.</p><p id="action"><strong>A / START: SEGUIR PARA A FASE 10A</strong></p></section><section class="card"><strong>Avaliação de UX</strong><ol><li>O nome da fase aparece diretamente, sem rótulos ou números antes dele.</li><li>Condição e consequência aparecem em frases completas, sem o termo “path”.</li><li>O texto principal é centralizado; os comandos ficam à direita, com margem de 8 px.</li><li>Uma linha vazia separa o texto do botão; a borda inferior mantém 8 px livres.</li><li>Desvios explicam o ocorrido, sem chamar perda do resgate de sucesso.</li></ol></section></div>
<section class="native"><img id="native" src="proposta-10a.png" alt="Prévia da proposta em 320 por 224 pixels"><p><strong>Conferência em 320 × 224.</strong><br>Mesma fonte de 8 × 8 do jogo, até 38 caracteres por linha e cores compatíveis com a interface. Os acentos aparecem no texto de apoio desta página; a prévia segue o conjunto de glifos atual da ROM.<br><br>O uso de duas cores no texto pode aproveitar PAL0/PAL3 nesta tela, sem duplicar a fonte. É uma proposta técnica; nenhum recurso do jogo foi modificado.</p></section>
<section><h2>Durante a viagem</h2><p>Ao iniciar o deslocamento, o comando muda para “A / START: PULAR VIAGEM”, alinhado à direita, na mesma margem do comando de seguir.</p><img class="travel" src="durante-viagem.png" alt="Proposta do comando durante a viagem: A ou Start para pular viagem"></section>
<footer><a href="antes-depois.png">Comparação ampliada</a> · <a href="proposta.json">Todos os textos e decisões de UX</a> · <a href="validacao-layout.json">Conferência de espaço e fonte</a><p>Proposta visual composta sobre capturas existentes. Não é captura de uma ROM modificada, não foi implementada e não foi testada em CRT.</p></footer></main>
<script>const cases='''+json.dumps(items,ensure_ascii=False)+''';for(const b of document.querySelectorAll('[data-case]'))b.addEventListener('click',()=>{for(const other of document.querySelectorAll('[data-case]'))other.setAttribute('aria-pressed',String(other===b));const c=cases[+b.dataset.case];document.getElementById('before').src=c.capture;document.getElementById('before').alt='Captura atual: '+c.label;for(const id of ['after','native']){document.getElementById(id).src=c.proposal;document.getElementById(id).alt='Proposta: '+c.label;}document.getElementById('destination').textContent=c.name;document.getElementById('cause').textContent=c.cause;document.getElementById('consequence').textContent=c.consequence;document.getElementById('action').textContent='A / START: SEGUIR PARA A FASE '+c.next;});</script></html>'''
 destination='proposta-aprovada.html' if data.get('status')=='implemented' else 'revisao.html'
 (ROOT/destination).write_text(page)
 print(json.dumps(report))

if __name__=='__main__':main()
