"""Check transparent logo compositing and menu restoration on the real ROM."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
ART=ROOT.parent

def hardware(image):
    hw=np.rint(np.asarray(image.convert('RGB')).astype(np.int32)*7/255).astype(np.int32)*34
    rgb=np.empty_like(hw)
    for channel,bits in enumerate((31,63,31)):
        rgb[:,:,channel]=(hw[:,:,channel]>>(2 if channel==1 else 3))*255//bits
    return rgb

def main():
    bg=hardware(Image.open(ART/'title-caatinga-v1/title-native.png'))
    logo=Image.open(ROOT/'logo-native.png')
    inks=np.asarray(logo)
    expected=bg.copy()
    patch=expected[:88,8:136]
    patch[inks!=0]=hardware(logo)[inks!=0]
    checks=[]
    for region in ('ntsc','pal'):
        for suffix in ('natural','skip','game','gallery','help'):
            p=ART/f'intro-monologo-v1/emulator-{region}/menu-after-{suffix}.png'
            image=np.asarray(Image.open(p))
            assert np.array_equal(image[:96],expected[:96]),(region,suffix,'menu logo/background mismatch')
            checks.append(dict(region=region,menu=suffix,logo_and_background_mismatches=0))
    report=dict(passed=True,logo_size=[128,88],logo_position=[8,0],transparent_index=0,checks=checks)
    (ROOT/'pixel-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: compact option B and transparent backdrop match in 10 real menu captures.')
if __name__=='__main__': main()
