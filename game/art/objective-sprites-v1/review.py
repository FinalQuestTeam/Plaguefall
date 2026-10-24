"""Reproducible technical previews from exported frames and emulator captures."""
from pathlib import Path
from PIL import Image, ImageDraw
from export import ASSETS

HERE=Path(__file__).resolve().parent
LABELS=['Ninho','Gerador','Caixa de detonadores','Transmissor','Válvula','Grade','Armadilha','Rádio','Civil (arquivo)','Câmara de contenção']


def main():
    frames=[]
    for pose in range(6):
        sheet=Image.new('RGB',(540,((len(ASSETS)+2)//3)*160),(27,34,32));draw=ImageDraw.Draw(sheet)
        for i,((name,w,h),label) in enumerate(zip(ASSETS,LABELS)):
            x=i%3*180;y=i//3*160
            draw.text((x+8,y+7),label,fill=(219,182,36))
            sprite=Image.open(HERE/f'frames/{name}-{pose}.png').convert('RGBA').resize((w*2,h*2),Image.Resampling.NEAREST)
            sheet.paste(sprite,(x+(180-w*2)//2,y+154-h*2),sprite)
        frames.append(sheet)
    frames[0].save(HERE/'preview-grid.gif',save_all=True,append_images=frames[1:],
                   duration=[750,300,200,200,200,900],loop=0)
    civilian=[]
    for pose in range(6):
        sprite=Image.open(HERE/f'frames/refugee-{pose}.png').convert('RGBA').resize((128,192),Image.Resampling.NEAREST)
        board=Image.new('RGB',(160,208),(27,34,32));board.paste(sprite,(16,8),sprite);civilian.append(board)
    civilian[0].save(HERE/'refugee-preview.gif',save_all=True,append_images=civilian[1:],
                     duration=[600,180,180,180,180,700],loop=0)
    preview=Image.new('RGB',(640,4*248),(27,34,32));draw=ImageDraw.Draw(preview)
    found=0
    for i,((name,w,h),label) in enumerate(zip(ASSETS[:8],LABELS[:8])):
        capture=HERE/f'validation/ntsc/animation-{i+11:02d}-{name}-frame-3.png'
        revised=HERE/f'validation/refugee-woman/ntsc/animation-{i+11:02d}-{name}-frame-3.png'
        if revised.exists():capture=revised
        mounted=HERE/f'validation/gate-mount/ntsc/animation-{i+11:02d}-{name}-frame-3.png'
        if mounted.exists():capture=mounted
        polished=HERE/f'validation/mission-polish/ntsc/animation-{i+11:02d}-{name}-frame-3.png'
        if polished.exists():capture=polished
        if not capture.exists():continue
        x=i%2*320;y=i//2*248;draw.text((x+6,y+5),f'{i+11}. {label}',fill=(219,182,36))
        preview.paste(Image.open(capture).convert('RGB'),(x,y+22));found+=1
    if found==8:preview.save(HERE/'emulator-actions.png')
    for state in ('closed','open'):
        paths=[HERE/f'validation/gate-mount/{revision}/gate-mount-{state}.png' for revision in ('before','ntsc')]
        if not all(p.exists() for p in paths):continue
        comparison=Image.new('RGB',(640,248),(27,34,32));draw=ImageDraw.Draw(comparison)
        for i,(path,label) in enumerate(zip(paths,['Antes: grade frontal','Depois: fechamento no eixo do muro'])):
            draw.text((i*320+6,6),label,fill=(219,182,36))
            comparison.paste(Image.open(path).convert('RGB'),(i*320,24))
        comparison.resize((1280,496),Image.Resampling.NEAREST).save(HERE/f'gate-mount-{state}-comparison.png')
    current=HERE/'validation/mission-polish/ntsc'
    views=[('generator-powered-pulse-4.png','12. Energia ligada: pulso contínuo'),
           ('cargo-open-bag-0.png','13. Baú aberto e sacola coletável'),
           ('gate-mount-open.png','16. Escolta de Dinorah no corredor'),
           ('containment-occupied-frame-3.png','17. Insetos retidos na câmara')]
    if all((current/name).exists() for name,_ in views):
        board=Image.new('RGB',(640,496),(27,34,32));draw=ImageDraw.Draw(board)
        for i,(name,label) in enumerate(views):
            x=i%2*320;y=i//2*248;draw.text((x+5,y+6),label,fill=(219,182,36))
            board.paste(Image.open(current/name).convert('RGB'),(x,y+24))
        board.save(HERE/'mission-polish-preview.png')
    sequence=[current/f'generator-powered-pulse-{i}.png' for i in (5,4,3,4)]
    if all(p.exists() for p in sequence):
        pulses=[Image.open(p).convert('RGB') for p in sequence]
        pulses[0].save(HERE/'generator-powered-preview.gif',save_all=True,append_images=pulses[1:],duration=250,loop=0)
    print('Uniform2x animated grid; native action captures:',found)


if __name__=='__main__':main()
